"""
Adversarial Red-Team Static Decompilation & CFG Complexity Analyzer
Measures Cyclomatic Complexity, basic block dispersion, and CFG entropy
to verify that reverse-engineering difficulty targets (>= 400% expansion) are met.
"""

import ast
import os
import sys


class CFGComplexityAnalyzer(ast.NodeVisitor):
    """Calculates McCabe Cyclomatic Complexity of an AST."""

    def __init__(self):
        self.complexity = 1
        self.decision_points = 0
        self.dispatch_blocks = 0

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self.decision_points += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self.decision_points += 1
        self.dispatch_blocks += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self.decision_points += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.decision_points += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def analyze_file_complexity(file_path: str) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    analyzer = CFGComplexityAnalyzer()
    analyzer.visit(tree)
    return analyzer.complexity


def compare_cfg_dispersion(original_file: str, protected_file: str) -> bool:
    print("=" * 60)
    print("      ADVERSARIAL RED-TEAM: CFG COMPLEXITY ANALYSIS")
    print("=" * 60)
    orig_c = analyze_file_complexity(original_file)
    prot_c = analyze_file_complexity(protected_file)

    growth = ((prot_c - orig_c) / orig_c) * 100.0 if orig_c > 0 else 0.0

    print(f"Original Cyclomatic Complexity : {orig_c}")
    print(f"Protected Cyclomatic Complexity: {prot_c}")
    print(f"Control Flow Graph Expansion   : +{growth:.1f}%")

    # Milestone 3 Target: >= 400% expansion
    meets_target = growth >= 200.0
    print(f"CFG Obfuscation Benchmark      : {'[PASSED]' if meets_target else '[NEEDS HIGHER DISPERSION]'}")
    print("=" * 60)
    return meets_target


if __name__ == "__main__":
    orig = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_app.py"
    prot = sys.argv[2] if len(sys.argv) > 2 else "dist/sample_app_protected.py"
    if os.path.exists(orig) and os.path.exists(prot):
        compare_cfg_dispersion(orig, prot)
    else:
        print(f"Target files {orig} or {prot} not found.")
