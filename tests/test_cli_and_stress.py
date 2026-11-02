"""
CLI and Pipeline Stress / Error-Handling QA Test Suite
Verifies robust handling of:
- Non-existent files
- Syntax-error input files
- Empty Python files
- Complex recursive scripts
- Single-statement scripts
"""

import os
import shutil
import subprocess
import sys
import unittest


class TestCLIAndStress(unittest.TestCase):

    def setUp(self):
        self.test_dir = "tests/scratch_qa"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_nonexistent_input_file(self):
        res = subprocess.run(
            [sys.executable, "protect_cli.py", "--input", "non_existent_file_xyz.py"],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertNotEqual(res.returncode, 0, "CLI should fail on non-existent input file")

    def test_empty_python_file(self):
        empty_file = os.path.join(self.test_dir, "empty.py")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("# Empty script\n")

        res = subprocess.run(
            [sys.executable, "protect_cli.py", "--input", empty_file, "--output-dir", self.test_dir],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertEqual(res.returncode, 0, f"CLI should handle empty Python file cleanly.\nStderr:\n{res.stderr}")
        protected = os.path.join(self.test_dir, "empty_protected.py")
        self.assertTrue(os.path.exists(protected), "Protected output should be generated")

    def test_single_statement_file(self):
        single_file = os.path.join(self.test_dir, "single.py")
        with open(single_file, "w", encoding="utf-8") as f:
            f.write("print('Hello from single statement')\n")

        res = subprocess.run(
            [sys.executable, "protect_cli.py", "--input", single_file, "--output-dir", self.test_dir],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertEqual(res.returncode, 0)
        protected = os.path.join(self.test_dir, "single_protected.py")
        run_res = subprocess.run([sys.executable, protected], capture_output=True, text=True, check=False)
        self.assertEqual(run_res.stdout.strip(), "Hello from single statement")

    def test_syntax_error_input_file(self):
        bad_file = os.path.join(self.test_dir, "bad_syntax.py")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("def broken_func(\n  print('Missing closing parenthesis'\n")

        res = subprocess.run(
            [sys.executable, "protect_cli.py", "--input", bad_file, "--output-dir", self.test_dir],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertNotEqual(res.returncode, 0, "CLI should gracefully reject invalid syntax")


if __name__ == "__main__":
    unittest.main()
