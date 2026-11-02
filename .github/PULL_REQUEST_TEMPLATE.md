## Description
<!-- Provide a concise description of the changes introduced by this PR -->

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Performance optimization
- [ ] Security hardening

## Pipeline Stage Affected
- [ ] AST Sanitizer (`engine/ast_engine/sanitizer.py`)
- [ ] Scope Analyzer (`engine/ast_engine/scope_analyzer.py`)
- [ ] Control Flow Flattener (`engine/ast_engine/flattener.py`)
- [ ] Symbol Mangler (`engine/ast_engine/mangler.py`)
- [ ] String Encryptor (`engine/ast_engine/string_encryptor.py`)
- [ ] Native C Subsystem (`engine/native_crypto/`)
- [ ] Nuitka Compiler Pipeline (`engine/pipeline/`)
- [ ] CLI / Packaging (`protect_cli.py`, `pyproject.toml`)

## Quality Checklist
- [ ] My code conforms to the project's style guidelines (`ruff check .`).
- [ ] I have added unit tests verifying 100% functional equivalence of AST transformations.
- [ ] All existing regression tests pass (`python -m unittest discover tests`).
- [ ] The adversarial benchmark suite passes:
  - [ ] CFG expansion >= +400% (`python qa/redteam_ghidra.py`)
  - [ ] Zero sensitive plaintext string leaks (`python qa/redteam_frida.py`)
  - [ ] Performance overhead within budget (`python qa/benchmark_suite.py`)
- [ ] Native C code compiles without warnings (`-Wall -Wextra`).
- [ ] I have updated documentation where appropriate (`README.md`, `docs/`).
