"""
Obfuscation Depth and String Encryption QA Test Suite
Validates that:
1. All string literals and print statements are encrypted into inline decryptors.
2. Function names, class names, method names, parameters, and attributes are mangled.
3. Functional equivalence and stdout output remain 100% identical.
"""

import ast
import io
import sys
import unittest

from engine.ast_engine.sanitizer import sanitize_ast
from engine.ast_engine.flattener import flatten_control_flow
from engine.ast_engine.mangler import mangle_symbols
from engine.ast_engine.string_encryptor import encrypt_strings


class TestObfuscationDepth(unittest.TestCase):

    def _execute(self, source_code: str, entry_call: str):
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        ns = {}
        try:
            exec(source_code, ns)
            res = eval(entry_call, ns)
        finally:
            sys.stdout = old_stdout
        return buf.getvalue(), res

    def test_string_literal_encryption(self):
        source = '''
def run_test():
    secret_key = "sk_live_9948291048201"
    banner = "WELCOME_TO_SYSTEM"
    print(banner)
    return secret_key
'''
        tree = ast.parse(source)
        tree = sanitize_ast(tree)
        tree = encrypt_strings(tree)
        obfuscated = ast.unparse(tree)

        # Assert no plaintext secrets exist in code
        self.assertNotIn("sk_live_9948291048201", obfuscated)
        self.assertNotIn("WELCOME_TO_SYSTEM", obfuscated)
        self.assertIn("_0xdec", obfuscated)

        # Assert runtime equivalence
        orig_out, orig_res = self._execute(source, "run_test()")
        obf_out, obf_res = self._execute(obfuscated, "run_test()")

        self.assertEqual(orig_res, "sk_live_9948291048201")
        self.assertEqual(orig_res, obf_res)
        self.assertEqual(orig_out, obf_out)

    def test_fstring_and_format_spec_encryption(self):
        source = '''
def run_test():
    score = 0.87654
    label = "ALPHA"
    msg = f"Result: [{label}] with precision {score:.2%}"
    print(msg)
    return msg
'''
        tree = ast.parse(source)
        tree = sanitize_ast(tree)
        tree = encrypt_strings(tree)
        obfuscated = ast.unparse(tree)

        self.assertNotIn("Result: [", obfuscated)
        self.assertNotIn("ALPHA", obfuscated)
        self.assertIn("_0xdec", obfuscated)

        orig_out, orig_res = self._execute(source, "run_test()")
        obf_out, obf_res = self._execute(obfuscated, "run_test()")

        self.assertEqual(orig_res, "Result: [ALPHA] with precision 87.65%")
        self.assertEqual(orig_res, obf_res)
        self.assertEqual(orig_out, obf_out)

    def test_class_method_and_attribute_mangling(self):
        source = '''
class ProprietaryAlgorithm:
    def __init__(self, seed_val: int):
        self.internal_seed = seed_val
        self.state_counter = 0

    def compute_next(self, step: int) -> int:
        self.state_counter += 1
        return (self.internal_seed * step) + self.state_counter

def run_test():
    algo = ProprietaryAlgorithm(seed_val=42)
    val1 = algo.compute_next(step=3)
    val2 = algo.compute_next(step=5)
    return val1 + val2
'''
        tree = ast.parse(source)
        tree = sanitize_ast(tree)
        tree = flatten_control_flow(tree)
        tree = mangle_symbols(tree, salt="qa_depth_salt", preserve_names={"run_test"})
        tree = encrypt_strings(tree)
        obfuscated = ast.unparse(tree)

        # Assert class, method, attribute, and parameter names are completely obfuscated
        self.assertNotIn("ProprietaryAlgorithm", obfuscated)
        self.assertNotIn("compute_next", obfuscated)
        self.assertNotIn("internal_seed", obfuscated)
        self.assertNotIn("state_counter", obfuscated)
        self.assertNotIn("seed_val", obfuscated)

        # Assert functional equivalence
        orig_out, orig_res = self._execute(source, "run_test()")
        obf_out, obf_res = self._execute(obfuscated, "run_test()")

        self.assertEqual(orig_res, (42 * 3 + 1) + (42 * 5 + 2))
        self.assertEqual(orig_res, obf_res)
        self.assertEqual(orig_out, obf_out)


if __name__ == "__main__":
    unittest.main()
