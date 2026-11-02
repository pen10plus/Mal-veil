"""
AST Obfuscation & Hardening Engine
"""

from .sanitizer import sanitize_ast
from .flattener import flatten_control_flow
from .mangler import mangle_symbols, SymbolMangler
from .string_encryptor import encrypt_strings, StringEncryptor

__all__ = [
    "sanitize_ast",
    "flatten_control_flow",
    "mangle_symbols",
    "SymbolMangler",
    "encrypt_strings",
    "StringEncryptor",
]
