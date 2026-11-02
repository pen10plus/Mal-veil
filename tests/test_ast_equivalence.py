"""
AST Equivalence Verification Test Suite
Validates that AST mutations preserve 100% functional equivalence of Python execution.
"""

import ast
import io
import sys
import unittest
from engine.ast_engine.sanitizer import sanitize_ast
from engine.ast_engine.mangler import mangle_symbols
from engine.ast_engine.flattener import flatten_control_flow


class TestASTEquivalence(unittest.TestCase):

    def _execute_code(self, source_code: str, entry_call: str):
        """Executes source code in an isolated dictionary namespace and returns stdout and result."""
        captured_out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_out
        namespace = {}
        try:
            exec(source_code, namespace)
            result = eval(entry_call, namespace)
        finally:
            sys.stdout = old_stdout
        return captured_out.getvalue(), result

    def _transform_and_compare(self, original_source: str, entry_call: str):
        """Transforms original source through the entire Phase 1 pipeline and asserts equivalence."""
        orig_out, orig_res = self._execute_code(original_source, entry_call)

        tree = ast.parse(original_source)
        # Step 1: Sanitize
        tree = sanitize_ast(tree)
        # Step 2: Flatten Control Flow
        tree = flatten_control_flow(tree, seed=42)
        # Step 3: Mangle Symbols
        tree = mangle_symbols(tree, salt="test_salt", preserve_names={"run_test", "main", "Calculator", "process_data"})

        transformed_source = ast.unparse(tree)

        trans_out, trans_res = self._execute_code(transformed_source, entry_call)

        self.assertEqual(orig_res, trans_res, f"Return value mismatch!\nTransformed code:\n{transformed_source}")
        self.assertEqual(orig_out, trans_out, "Standard output mismatch!")
        return transformed_source

    def test_arithmetic_and_loops(self):
        code = '''
def run_test():
    """Computes sum of squares with math operations."""
    total: int = 0
    for i in range(1, 10):
        total += i * i
    print(f"Total computed: {total}")
    return total
'''
        self._transform_and_compare(code, "run_test()")

    def test_conditionals_and_branches(self):
        code = '''
def run_test():
    """Tests complex branching logic."""
    x = 15
    result = []
    if x > 10:
        result.append("greater")
    else:
        result.append("lesser")
    
    y = x * 2
    if y == 30:
        result.append("exact")
    return "-".join(result)
'''
        self._transform_and_compare(code, "run_test()")

    def test_recursion_and_state(self):
        code = '''
def run_test():
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    return fib(8)
'''
        self._transform_and_compare(code, "run_test()")

    def test_class_and_methods(self):
        code = '''
class Calculator:
    """A sample calculator class."""
    def __init__(self, base: int = 10):
        self.base = base
        
    def compute(self, multiplier: int) -> int:
        val = self.base * multiplier
        val += 5
        return val

def run_test():
    calc = Calculator(20)
    return calc.compute(3)
'''
        self._transform_and_compare(code, "run_test()")

    def test_docstring_and_type_stripping(self):
        code = '''
def run_test():
    """This docstring must be stripped."""
    x: int = 100
    y: str = "hello"
    return x
'''
        tree = ast.parse(code)
        sanitized = sanitize_ast(tree)
        unparsed = ast.unparse(sanitized)
        self.assertNotIn("This docstring must be stripped", unparsed)
        self.assertNotIn(": int", unparsed)

    def test_exception_handling(self):
        code = '''
def run_test():
    attempts = 0
    status = "failed"
    try:
        attempts += 1
        raise ValueError("simulated failure")
    except ValueError as err:
        attempts += 2
        status = "recovered"
    finally:
        attempts += 10
    return f"{status}-{attempts}"
'''
        self._transform_and_compare(code, "run_test()")

    def test_dictionary_comprehensions_and_kwargs(self):
        code = '''
def process_data(multiplier=2, **kwargs):
    result = {k: v * multiplier for k, v in kwargs.items()}
    items = sorted(result.items())
    return items

def run_test():
    return process_data(multiplier=3, alpha=10, beta=20, gamma=30)
'''
        self._transform_and_compare(code, "run_test()")


if __name__ == "__main__":
    unittest.main()
