"""
Symbol & Identifier Mangling Module
Renames internal variables, class names, methods, parameters, and attributes to opaque hex hashes.
Preserves Python built-ins, standard libraries, entrypoints, imported modules, dunders, and standard attributes.
"""

import ast
import hashlib
from typing import Dict, List, Optional, Set
from .scope_analyzer import ScopeAnalyzer


STANDARD_ATTRS = {
    # Sequence & collection methods
    "append", "extend", "insert", "remove", "pop", "clear", "index", "count",
    "sort", "reverse", "copy", "keys", "values", "items", "get", "update",
    "setdefault", "fromkeys", "popitem",
    # String manipulation
    "split", "rsplit", "splitlines", "join", "replace", "startswith", "endswith",
    "lower", "upper", "title", "capitalize", "strip", "lstrip", "rstrip",
    "encode", "decode", "format", "format_map", "find", "rfind", "center",
    "ljust", "rjust", "zfill", "partition", "rpartition", "translate", "maketrans",
    "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isidentifier",
    "islower", "isnumeric", "isprintable", "isspace", "istitle", "isupper",
    # IO & File operations
    "read", "readline", "readlines", "write", "writelines", "close", "seek",
    "tell", "flush", "closed", "readable", "writable", "seekable",
    # OS / Sys / Runtime / Subprocess
    "sleep", "perf_counter", "time", "monotonic", "executable", "argv", "path",
    "exit", "stdout", "stderr", "stdin", "run", "Popen", "capture_output",
    "check", "returncode", "communicate", "poll", "wait", "terminate", "kill",
    # Set operations
    "add", "discard", "union", "intersection", "difference", "symmetric_difference",
    "issubset", "issuperset", "isdisjoint",
    # Coroutines / Generators
    "send", "throw",
    # Properties & decorators
    "getter", "setter", "deleter"
}

STANDARD_KWARGS = {
    "key", "reverse", "default", "encoding", "errors", "mode", "file", "flush",
    "sep", "end", "capture_output", "text", "check", "stdout", "stderr", "stdin",
    "shell", "timeout", "cwd", "env", "input", "args", "kwargs"
}


def collect_imported_symbols(tree: ast.AST) -> Set[str]:
    """Collects all module names and imported symbols so they are never accidentally mangled."""
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    return imported


def collect_user_parameters(tree: ast.AST) -> Set[str]:
    """Collects explicitly declared parameter names of all functions and methods in the module."""
    params = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                params.add(arg.arg)
            for arg in getattr(node.args, "posonlyargs", []):
                params.add(arg.arg)
            for arg in node.args.kwonlyargs:
                params.add(arg.arg)
    return params


class SymbolMangler(ast.NodeTransformer):
    """
    Renames identifier symbols, classes, methods, parameters, and attributes to opaque hashes.
    Guarantees that built-ins, standard libraries, entrypoints, and lexical scopes are preserved.
    """

    def __init__(
        self,
        salt: str = "v2_hardened_salt",
        preserve_names: Optional[Set[str]] = None,
        user_params: Optional[Set[str]] = None
    ):
        self.salt = salt
        self.preserve_names = set(preserve_names or set()) | ScopeAnalyzer.BUILTIN_NAMES | {
            "main", "__name__", "__main__", "__init__", "__del__", "__repr__",
            "__str__", "__bytes__", "__format__", "__lt__", "__le__", "__eq__",
            "__ne__", "__gt__", "__ge__", "__hash__", "__bool__", "__getattr__",
            "__getattribute__", "__setattr__", "__delattr__", "__dir__",
            "__get__", "__set__", "__delete__", "__init_subclass__",
            "__call__", "__len__", "__getitem__", "__setitem__", "__delitem__",
            "__iter__", "__next__", "__enter__", "__exit__", "__aenter__", "__aexit__",
            "self", "cls", "_0xdec"
        }
        self.user_params = set(user_params or set())
        self.mapping: Dict[str, str] = {}
        self._scope_stack: List[Dict[str, str]] = [{}]

    def _hash_name(self, original_name: str) -> str:
        """Derives a deterministic, high-entropy variable name from original name and salt."""
        digest = hashlib.sha256(f"{self.salt}_{original_name}".encode("utf-8")).hexdigest()[:8]
        return f"_0x{digest}"

    def _should_preserve(self, name: str) -> bool:
        """Returns True if the name should not be mangled."""
        if not name:
            return True
        if name in self.preserve_names:
            return True
        if name.startswith("__") and name.endswith("__"):
            return True
        return False

    def _collect_local_names(self, node: ast.AST) -> Set[str]:
        """Collects all names assigned strictly in the immediate function scope."""
        assigned = set()
        explicit_globals = set()
        explicit_nonlocals = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Global):
                explicit_globals.update(child.names)
            elif isinstance(child, ast.Nonlocal):
                explicit_nonlocals.update(child.names)

        def walk_non_subscopes(n):
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    assigned.add(child.name)
                    continue
                if isinstance(child, (ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                    continue
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    if child.id not in explicit_globals and child.id not in explicit_nonlocals:
                        assigned.add(child.id)
                walk_non_subscopes(child)

        walk_non_subscopes(node)
        return assigned

    def _get_mangled_name(self, name: str, create: bool = False) -> str:
        if self._should_preserve(name):
            return name

        for scope in reversed(self._scope_stack):
            if name in scope:
                return scope[name]

        if create:
            mangled = self._hash_name(name)
            self._scope_stack[-1][name] = mangled
            self.mapping[name] = mangled
            return mangled

        if name in self.mapping:
            return self.mapping[name]

        return self._hash_name(name)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if not self._should_preserve(node.name):
            mangled_class = self._hash_name(node.name)
            self._scope_stack[-1][node.name] = mangled_class
            self.mapping[node.name] = mangled_class
            node.name = mangled_class

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if not self._should_preserve(node.name):
            mangled_func = self._hash_name(node.name)
            self._scope_stack[-1][node.name] = mangled_func
            self.mapping[node.name] = mangled_func
            node.name = mangled_func

        new_scope: Dict[str, str] = {}
        self._scope_stack.append(new_scope)

        # Mangle declared parameters
        for arg in node.args.args:
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg
        for arg in getattr(node.args, "posonlyargs", []):
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg
        for arg in node.args.kwonlyargs:
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg
        if node.args.vararg and not self._should_preserve(node.args.vararg.arg):
            mangled_v = self._hash_name(node.args.vararg.arg)
            new_scope[node.args.vararg.arg] = mangled_v
            node.args.vararg.arg = mangled_v
        if node.args.kwarg and not self._should_preserve(node.args.kwarg.arg):
            mangled_k = self._hash_name(node.args.kwarg.arg)
            new_scope[node.args.kwarg.arg] = mangled_k
            node.args.kwarg.arg = mangled_k

        # Collect and mangle local variables
        local_assigned = self._collect_local_names(node)
        for var_name in local_assigned:
            if not self._should_preserve(var_name) and var_name not in new_scope:
                new_scope[var_name] = self._hash_name(var_name)

        self.generic_visit(node)
        self._scope_stack.pop()
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        if not self._should_preserve(node.name):
            mangled_func = self._hash_name(node.name)
            self._scope_stack[-1][node.name] = mangled_func
            self.mapping[node.name] = mangled_func
            node.name = mangled_func

        new_scope: Dict[str, str] = {}
        self._scope_stack.append(new_scope)

        for arg in node.args.args:
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg
        for arg in getattr(node.args, "posonlyargs", []):
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg
        for arg in node.args.kwonlyargs:
            if not self._should_preserve(arg.arg):
                mangled_arg = self._hash_name(arg.arg)
                new_scope[arg.arg] = mangled_arg
                arg.arg = mangled_arg

        local_assigned = self._collect_local_names(node)
        for var_name in local_assigned:
            if not self._should_preserve(var_name) and var_name not in new_scope:
                new_scope[var_name] = self._hash_name(var_name)

        self.generic_visit(node)
        self._scope_stack.pop()
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.visit(node.value)
        if not self._should_preserve(node.attr) and node.attr not in STANDARD_ATTRS:
            node.attr = self._hash_name(node.attr)
        return node

    def visit_keyword(self, node: ast.keyword) -> ast.AST:
        self.visit(node.value)
        # Only mangle keyword argument if it matches an explicitly declared user parameter
        if node.arg and node.arg in self.user_params and not self._should_preserve(node.arg) and node.arg not in STANDARD_KWARGS:
            node.arg = self._hash_name(node.arg)
        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.AST:
        lambda_scope: Dict[str, str] = {}
        self._scope_stack.append(lambda_scope)
        for arg in node.args.args:
            lambda_scope[arg.arg] = arg.arg
        for arg in getattr(node.args, "posonlyargs", []):
            lambda_scope[arg.arg] = arg.arg
        for arg in node.args.kwonlyargs:
            lambda_scope[arg.arg] = arg.arg
        if node.args.vararg:
            lambda_scope[node.args.vararg.arg] = node.args.vararg.arg
        if node.args.kwarg:
            lambda_scope[node.args.kwarg.arg] = node.args.kwarg.arg

        self.generic_visit(node)
        self._scope_stack.pop()
        return node

    def _visit_comprehension(self, node: ast.AST) -> ast.AST:
        comp_scope: Dict[str, str] = {}
        self._scope_stack.append(comp_scope)
        for gen in getattr(node, "generators", []):
            for child in ast.walk(gen.target):
                if isinstance(child, ast.Name):
                    comp_scope[child.id] = child.id
        self.generic_visit(node)
        self._scope_stack.pop()
        return node

    def visit_ListComp(self, node: ast.ListComp) -> ast.AST:
        return self._visit_comprehension(node)

    def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
        return self._visit_comprehension(node)

    def visit_SetComp(self, node: ast.SetComp) -> ast.AST:
        return self._visit_comprehension(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> ast.AST:
        return self._visit_comprehension(node)

    def visit_Global(self, node: ast.Global) -> ast.AST:
        new_names = []
        for name in node.names:
            module_scope = self._scope_stack[0]
            if name in module_scope:
                new_names.append(module_scope[name])
            else:
                new_names.append(name)
        node.names = new_names
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.AST:
        new_names = []
        for name in node.names:
            mangled = self._get_mangled_name(name, create=False)
            new_names.append(mangled)
        node.names = new_names
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Store):
            node.id = self._get_mangled_name(node.id, create=True)
        elif isinstance(node.ctx, (ast.Load, ast.Del)):
            node.id = self._get_mangled_name(node.id, create=False)
        return node


def mangle_symbols(tree: ast.AST, salt: str = "v2_hardened_salt", preserve_names: Optional[Set[str]] = None) -> ast.AST:
    """Convenience helper to mangle AST symbols in place with imported symbol and parameter awareness."""
    imported_symbols = collect_imported_symbols(tree)
    user_parameters = collect_user_parameters(tree)
    full_preserve = set(preserve_names or set()) | imported_symbols
    mangler = SymbolMangler(salt=salt, preserve_names=full_preserve, user_params=user_parameters)
    mangled_tree = mangler.visit(tree)
    ast.fix_missing_locations(mangled_tree)
    return mangled_tree
