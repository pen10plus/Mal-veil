"""
Python Hardened Protection Engine (v2.0)
High-assurance source-to-source obfuscation, ephemeral C99 cryptography,
and native binary compilation toolchain.
"""

__version__ = "2.0.0"
__author__ = "Hardened Protection Engine Contributors"
__license__ = "MIT"

from engine.ast_engine.sanitizer import sanitize_ast
from engine.ast_engine.flattener import flatten_control_flow
from engine.ast_engine.mangler import mangle_symbols
from engine.ast_engine.string_encryptor import encrypt_strings
from engine.pipeline.compiler import BuildDriver

__all__ = [
    "sanitize_ast",
    "flatten_control_flow",
    "mangle_symbols",
    "encrypt_strings",
    "BuildDriver",
    "__version__",
]
