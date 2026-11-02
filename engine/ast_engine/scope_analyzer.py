"""
Scope Analyzer Module
Constructs a lexical scope tree to determine safe variable renaming boundaries.
"""

import ast
import builtins
from typing import Dict, List, Optional, Set


class Scope:
    """Represents a lexical scope (module, class, function, or comprehension)."""

    def __init__(self, name: str, scope_type: str, parent: Optional["Scope"] = None):
        self.name = name
        self.scope_type = scope_type  # 'module', 'class', 'function', 'comprehension'
        self.parent = parent
        self.children: List["Scope"] = []
        
        self.defs: Set[str] = set()       # Defined locally
        self.uses: Set[str] = set()       # Read or referenced
        self.globals: Set[str] = set()    # Declared with 'global'
        self.nonlocals: Set[str] = set()  # Declared with 'nonlocal'

    def is_local(self, var_name: str) -> bool:
        """Determines if a variable name is strictly local to this scope."""
        if var_name in self.globals or var_name in self.nonlocals:
            return False
        return var_name in self.defs

    def lookup_scope(self, var_name: str) -> Optional["Scope"]:
        """Walks up the scope hierarchy to find the enclosing scope that defined var_name."""
        curr: Optional["Scope"] = self
        while curr:
            if var_name in curr.defs:
                return curr
            curr = curr.parent
        return None


class ScopeAnalyzer(ast.NodeVisitor):
    """Walks the AST and builds a comprehensive Scope tree."""

    BUILTIN_NAMES = set(dir(builtins)) | {
        "__name__", "__file__", "__doc__", "__package__", "__spec__",
        "__path__", "__loader__", "__builtins__", "__class__"
    }

    def __init__(self):
        self.current_scope = Scope(name="__main__", scope_type="module")
        self.module_scope = self.current_scope

    def _enter_scope(self, name: str, scope_type: str) -> Scope:
        new_scope = Scope(name=name, scope_type=scope_type, parent=self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        return new_scope

    def _exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.current_scope.defs.add(node.name)
        scope = self._enter_scope(node.name, "function")
        
        # Add parameter names as local definitions
        for arg in node.args.args:
            scope.defs.add(arg.arg)
        for arg in node.args.kwonlyargs:
            scope.defs.add(arg.arg)
        for arg in getattr(node.args, "posonlyargs", []):
            scope.defs.add(arg.arg)
        if node.args.vararg:
            scope.defs.add(node.args.vararg.arg)
        if node.args.kwarg:
            scope.defs.add(node.args.kwarg.arg)

        # Visit body
        for stmt in node.body:
            self.visit(stmt)
        self._exit_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.current_scope.defs.add(node.name)
        scope = self._enter_scope(node.name, "function")
        for arg in node.args.args:
            scope.defs.add(arg.arg)
        for arg in node.args.kwonlyargs:
            scope.defs.add(arg.arg)
        for arg in getattr(node.args, "posonlyargs", []):
            scope.defs.add(arg.arg)
        if node.args.vararg:
            scope.defs.add(node.args.vararg.arg)
        if node.args.kwarg:
            scope.defs.add(node.args.kwarg.arg)

        for stmt in node.body:
            self.visit(stmt)
        self._exit_scope()

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_scope.defs.add(node.name)
        self._enter_scope(node.name, "class")
        for stmt in node.body:
            self.visit(stmt)
        self._exit_scope()

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self.current_scope.globals.add(name)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.current_scope.nonlocals.add(name)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            if node.id not in self.current_scope.globals and node.id not in self.current_scope.nonlocals:
                self.current_scope.defs.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.current_scope.uses.add(node.id)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            bound_name = alias.asname or alias.name.split(".")[0]
            self.current_scope.defs.add(bound_name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name != "*":
                bound_name = alias.asname or alias.name
                self.current_scope.defs.add(bound_name)


def analyze_scopes(tree: ast.AST) -> Scope:
    """Performs scope analysis and returns the root module scope."""
    analyzer = ScopeAnalyzer()
    analyzer.visit(tree)
    return analyzer.module_scope
