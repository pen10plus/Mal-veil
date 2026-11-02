"""
Comprehensive Advanced QA Test Suite
Stress-tests the protection engine against complex Python language features:
- Global & nonlocal variable mutations
- Generators (yield, yield from)
- Coroutines (async/await)
- Decorators (@property, @staticmethod, custom decorators)
- Internal keyword arguments (func(param=val))
- Tuple unpacking & variadic arguments (*args, **kwargs)
- Class inheritance & super() delegation
- Context managers (with ... as ...)
- Nested lambda expressions & higher-order functions
"""

import ast
import asyncio
import io
import sys
import unittest
from engine.ast_engine.sanitizer import sanitize_ast
from engine.ast_engine.mangler import mangle_symbols
from engine.ast_engine.flattener import flatten_control_flow


class TestAdvancedQA(unittest.TestCase):

    def _execute_code(self, source_code: str, entry_call: str):
        """Executes code in an isolated namespace and returns stdout and result."""
        captured_out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_out
        namespace = {}
        try:
            exec(source_code, namespace)
            result = eval(entry_call, namespace)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
        finally:
            sys.stdout = old_stdout
        return captured_out.getvalue(), result

    def _transform_and_verify(self, source: str, entry_call: str, preserve: set = None):
        """Transforms source through full pipeline and checks equivalence."""
        if preserve is None:
            preserve = {"run_test", "main"}
            
        orig_out, orig_res = self._execute_code(source, entry_call)

        tree = ast.parse(source)
        tree = sanitize_ast(tree)
        tree = flatten_control_flow(tree, seed=777)
        tree = mangle_symbols(tree, salt="qa_salt_2026", preserve_names=preserve)

        transformed = ast.unparse(tree)

        trans_out, trans_res = self._execute_code(transformed, entry_call)

        self.assertEqual(orig_res, trans_res, f"Return value mismatch!\nTransformed:\n{transformed}")
        self.assertEqual(orig_out, trans_out, "Output mismatch!")
        return transformed

    def test_global_variable_mutation(self):
        code = '''
global_counter = 50

def run_test():
    global global_counter
    global_counter += 25
    local_val = global_counter * 2
    return local_val
'''
        self._transform_and_verify(code, "run_test()")

    def test_generators_and_yield(self):
        code = '''
def run_test():
    def count_up(limit):
        n = 1
        while n <= limit:
            yield n * 10
            n += 1
    return list(count_up(4))
'''
        self._transform_and_verify(code, "run_test()")

    def test_decorators_property_and_methods(self):
        code = '''
class Account:
    def __init__(self, initial: float):
        self._balance = initial

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, val):
        self._balance = val

    @staticmethod
    def calculate_interest(principal, rate):
        return principal * rate

def run_test():
    acc = Account(100.0)
    acc.balance = 200.0
    interest = Account.calculate_interest(acc.balance, 0.05)
    return acc.balance + interest
'''
        self._transform_and_verify(code, "run_test()", preserve={"run_test", "Account"})

    def test_class_inheritance_and_super(self):
        code = '''
class BaseWorker:
    def __init__(self, role):
        self.role = role
    def work(self):
        return f"Working as {self.role}"

class LeadWorker(BaseWorker):
    def __init__(self, role, team_size):
        super().__init__(role)
        self.team_size = team_size
    def work(self):
        base_desc = super().work()
        return f"{base_desc} with team of {self.team_size}"

def run_test():
    worker = LeadWorker("Architect", 8)
    return worker.work()
'''
        self._transform_and_verify(code, "run_test()", preserve={"run_test", "BaseWorker", "LeadWorker"})

    def test_context_managers_with(self):
        code = '''
class Resource:
    def __init__(self):
        self.log = []
    def __enter__(self):
        self.log.append("entered")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.append("exited")
        return False
    def action(self):
        self.log.append("acted")

def run_test():
    res = Resource()
    with res as r:
        r.action()
    return "-".join(res.log)
'''
        self._transform_and_verify(code, "run_test()", preserve={"run_test", "Resource"})

    def test_tuple_unpacking_and_variadic(self):
        code = '''
def run_test():
    def compute(first, *args, multiplier=2, **kwargs):
        s = first + sum(args)
        bonus = sum(kwargs.values())
        return (s + bonus) * multiplier
    
    a, b, *rest = [1, 2, 3, 4, 5]
    return compute(a, b, *rest, multiplier=3, x=10, y=20)
'''
        self._transform_and_verify(code, "run_test()")

    def test_lambdas_and_closures(self):
        code = '''
def run_test():
    def make_adder(n):
        return lambda x: x + n
    add_five = make_adder(5)
    numbers = [1, 2, 3, 4]
    squared = list(map(lambda x: x * x, numbers))
    augmented = [add_five(x) for x in squared]
    return augmented
'''
        self._transform_and_verify(code, "run_test()")

    def test_async_coroutines(self):
        code = '''
import asyncio

async def run_test():
    async def async_calc(val):
        await asyncio.sleep(0.001)
        return val * 10
    
    res1 = await async_calc(3)
    res2 = await async_calc(7)
    return res1 + res2
'''
        self._transform_and_verify(code, "run_test()")


if __name__ == "__main__":
    unittest.main()
