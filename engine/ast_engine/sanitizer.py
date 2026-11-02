"""
AST Sanitization Module
Strips docstrings, type annotations, and compiler hints from Python ASTs.
"""

import ast
from typing import List, Optional


class ASTSanitizer(ast.NodeTransformer):
    """
    Traverses the AST and removes docstrings, type annotations, and debug metadata.
    Preserves exact runtime execution semantics.
    """

    def _strip_docstring(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """Removes the leading string constant expression statement if it exists."""
        if not body:
            return [ast.Pass()]
        
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                body = body[1:]
        
        if not body:
            return [ast.Pass()]
        return body

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        node.type_ignores = []
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        node.returns = None
        node.type_comment = None
        
        # Clean arguments annotations
        for arg in node.args.args:
            arg.annotation = None
            arg.type_comment = None
        for arg in node.args.kwonlyargs:
            arg.annotation = None
            arg.type_comment = None
        for arg in getattr(node.args, "posonlyargs", []):
            arg.annotation = None
            arg.type_comment = None
        if node.args.vararg:
            node.args.vararg.annotation = None
            node.args.vararg.type_comment = None
        if node.args.kwarg:
            node.args.kwarg.annotation = None
            node.args.kwarg.type_comment = None
            
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        node.returns = None
        node.type_comment = None
        
        for arg in node.args.args:
            arg.annotation = None
            arg.type_comment = None
        for arg in node.args.kwonlyargs:
            arg.annotation = None
            arg.type_comment = None
        for arg in getattr(node.args, "posonlyargs", []):
            arg.annotation = None
            arg.type_comment = None
        if node.args.vararg:
            node.args.vararg.annotation = None
            node.args.vararg.type_comment = None
        if node.args.kwarg:
            node.args.kwarg.annotation = None
            node.args.kwarg.type_comment = None
            
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        """Converts annotated assignment (x: int = 1) to regular assignment (x = 1)."""
        self.generic_visit(node)
        if node.value is not None:
            new_node = ast.Assign(
                targets=[node.target],
                value=node.value,
                lineno=node.lineno,
                col_offset=node.col_offset
            )
            return ast.copy_location(new_node, node)
        else:
            # Standalone type declaration (x: int) without value has no runtime effect in Python
            pass_node = ast.Pass(lineno=node.lineno, col_offset=node.col_offset)
            return ast.copy_location(pass_node, node)


def sanitize_ast(tree: ast.AST) -> ast.AST:
    """Convenience helper to sanitize an AST in-place."""
    sanitizer = ASTSanitizer()
    sanitized = sanitizer.visit(tree)
    ast.fix_missing_locations(sanitized)
    return sanitized
