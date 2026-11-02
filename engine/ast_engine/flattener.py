"""
Control Flow Flattening Module
Flattens function bodies into state-machine dispatch loops with hashed state transitions.
"""

import ast
import random
from typing import List, Tuple


class ControlFlowFlattener(ast.NodeTransformer):
    """
    Transforms basic statement sequences into a state-driven while-loop.
    Scrambles block sequence order in source to destroy sequential decompilation.
    """

    def __init__(self, seed: int = 1337):
        self.rng = random.Random(seed)

    def _contains_yield_or_await(self, node: ast.AST) -> bool:
        """Checks if a node contains yield, yield from, or await (Risk R-04 mitigation)."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom, ast.Await)):
                return True
        return False

    def _create_opaque_predicate(self) -> ast.AST:
        """
        Generates an invariant mathematical predicate that always evaluates to True at runtime:
        e.g., (len([]) * 17 + 1) > 0  or  ((len(__name__) * 2) % 2 == 0)
        """
        # Always true: (len(__name__) * 2) % 2 == 0
        predicate = ast.Compare(
            left=ast.BinOp(
                left=ast.BinOp(
                    left=ast.Call(
                        func=ast.Name(id="len", ctx=ast.Load()),
                        args=[ast.Name(id="__name__", ctx=ast.Load())],
                        keywords=[]
                    ),
                    op=ast.Mult(),
                    right=ast.Constant(value=2)
                ),
                op=ast.Mod(),
                right=ast.Constant(value=2)
            ),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)]
        )
        return predicate

    def _flatten_statements(self, statements: List[ast.stmt]) -> List[ast.stmt]:
        """Partitions statements into basic blocks and wraps them in a state-machine dispatcher."""
        if len(statements) < 2:
            return statements

        # Generate unique random state identifiers
        num_blocks = len(statements)
        state_ids = [self.rng.randint(0x1000, 0x7FFF) for _ in range(num_blocks)]
        # Ensure state IDs are completely unique
        while len(set(state_ids)) < num_blocks:
            state_ids = [self.rng.randint(0x1000, 0x7FFF) for _ in range(num_blocks)]
            
        exit_state = 0x9999

        # Build blocks: each block executes its statement and updates state to the next state
        blocks: List[Tuple[int, List[ast.stmt]]] = []
        for i in range(num_blocks):
            current_state = state_ids[i]
            next_state = state_ids[i + 1] if i + 1 < num_blocks else exit_state
            
            stmt = statements[i]
            
            # If the statement is already a return, we do not need to update state
            if isinstance(stmt, ast.Return):
                block_body = [stmt]
            else:
                state_update = ast.Assign(
                    targets=[ast.Name(id="_state", ctx=ast.Store())],
                    value=ast.Constant(value=next_state)
                )
                block_body = [stmt, state_update]
                
            blocks.append((current_state, block_body))

        # Scramble the physical order of blocks
        scrambled_blocks = list(blocks)
        self.rng.shuffle(scrambled_blocks)

        # Construct the if-elif-else ladder
        dispatch_if: ast.If = None
        current_if: ast.If = None

        for state_val, block_stmts in scrambled_blocks:
            test_condition = ast.Compare(
                left=ast.Name(id="_state", ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=state_val)]
            )
            
            new_if = ast.If(
                test=test_condition,
                body=block_stmts,
                orelse=[]
            )
            
            if dispatch_if is None:
                dispatch_if = new_if
                current_if = new_if
            else:
                current_if.orelse = [new_if]
                current_if = new_if

        # Add a fallthrough safety break in the innermost else
        if current_if:
            current_if.orelse = [ast.Break()]

        # Wrap in: _state = state_ids[0]; while _state != exit_state: ...
        init_state = ast.Assign(
            targets=[ast.Name(id="_state", ctx=ast.Store())],
            value=ast.Constant(value=state_ids[0])
        )
        
        loop_test = ast.Compare(
            left=ast.Name(id="_state", ctx=ast.Load()),
            ops=[ast.NotEq()],
            comparators=[ast.Constant(value=exit_state)]
        )
        
        # Inject an opaque predicate check into the while loop test
        # while (_state != exit_state) and opaque_predicate:
        compound_test = ast.BoolOp(
            op=ast.And(),
            values=[loop_test, self._create_opaque_predicate()]
        )
        
        while_loop = ast.While(
            test=compound_test,
            body=[dispatch_if],
            orelse=[]
        )

        return [init_state, while_loop]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        # Skip flattening if the function contains yield or await
        if self._contains_yield_or_await(node):
            return node
        
        node.body = self._flatten_statements(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        if self._contains_yield_or_await(node):
            return node
        
        node.body = self._flatten_statements(node.body)
        return node


def flatten_control_flow(tree: ast.AST, seed: int = 1337) -> ast.AST:
    """Convenience helper to apply control-flow flattening to an AST."""
    flattener = ControlFlowFlattener(seed=seed)
    flattened_tree = flattener.visit(tree)
    ast.fix_missing_locations(flattened_tree)
    return flattened_tree
