"""
String Encryption Module
Transforms plaintext string literals and f-strings (JoinedStr) into encrypted byte payloads
with an inline zero-dependency rolling XOR/ChaCha-inspired stream decryptor.
"""

import ast
from typing import Optional


def _encrypt_bytes(s: str, key: int = 0x5A) -> bytes:
    """Encrypts a string into bytes using a deterministic rolling key schedule."""
    raw = s.encode("utf-8")
    return bytes(b ^ ((key + (i * 37)) & 0xFF) for i, b in enumerate(raw))


class StringEncryptor(ast.NodeTransformer):
    """
    AST transformer that encrypts all string constants and f-string components.
    Injects a runtime zero-dependency in-memory decryption routine (_0xdec).
    """

    def __init__(self, key: int = 0x5A, decryptor_name: str = "_0xdec"):
        self.key = key
        self.decryptor_name = decryptor_name
        self._in_format_spec = False
        self._has_encrypted_strings = False

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        """Encrypts string constant components of f-strings without breaking format specifiers."""
        if self._in_format_spec:
            return node

        new_values = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                if not val.value:
                    new_values.append(val)
                    continue
                self._has_encrypted_strings = True
                ct = _encrypt_bytes(val.value, self.key)
                decrypt_call = ast.Call(
                    func=ast.Name(id=self.decryptor_name, ctx=ast.Load()),
                    args=[ast.Constant(value=ct), ast.Constant(value=self.key)],
                    keywords=[]
                )
                new_values.append(ast.FormattedValue(value=decrypt_call, conversion=-1))
            elif isinstance(val, ast.FormattedValue):
                # Recursively visit the inner expression
                val.value = self.visit(val.value)
                # Keep format_spec untouched to preserve Python formatting semantics (e.g. :.2%)
                new_values.append(val)
            else:
                new_values.append(self.visit(val))

        node.values = new_values
        return node

    def visit_FormattedValue(self, node: ast.FormattedValue) -> ast.AST:
        """Visits expression while guarding format specifier from encryption."""
        node.value = self.visit(node.value)
        # Never encrypt format_spec string literals
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Encrypts string constants into inline decryptor calls."""
        if isinstance(node.value, str) and not self._in_format_spec:
            if not node.value:
                return node
            self._has_encrypted_strings = True
            ct = _encrypt_bytes(node.value, self.key)
            decrypt_call = ast.Call(
                func=ast.Name(id=self.decryptor_name, ctx=ast.Load()),
                args=[ast.Constant(value=ct), ast.Constant(value=self.key)],
                keywords=[]
            )
            return decrypt_call
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        """Processes the module and injects decryptor helper at top."""
        self.generic_visit(node)
        if self._has_encrypted_strings:
            decryptor_ast = ast.parse(
                f"def {self.decryptor_name}(_0xct, _0xk):\n"
                f"    return bytes((_0xb ^ _0xk + _0xi * 37 & 255 for _0xi, _0xb in enumerate(_0xct))).decode('utf-8')\n"
            ).body[0]
            node.body.insert(0, decryptor_ast)
        return node


def encrypt_strings(tree: ast.AST, key: int = 0x5A) -> ast.AST:
    """Convenience helper to encrypt all strings within an AST."""
    transformer = StringEncryptor(key=key)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return transformed_tree
