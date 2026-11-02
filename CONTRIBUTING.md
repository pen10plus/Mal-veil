# Contributing to Python Hardened Protection Engine

Thank you for your interest in contributing to the **Python Hardened Protection Engine**! We welcome bug reports, security disclosures, architectural suggestions, performance optimizations, and code enhancements from the community.

Please take a few moments to review these guidelines before submitting an issue or pull request.

---

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Development Environment Setup](#development-environment-setup)
3. [Repository Architecture](#repository-architecture)
4. [Testing & Quality Assurance](#testing--quality-assurance)
5. [Code Style & Standards](#code-style--standards)
6. [Commit Message Conventions](#commit-message-conventions)
7. [Submitting a Pull Request](#submitting-a-pull-request)
8. [Reporting Security Vulnerabilities](#reporting-security-vulnerabilities)

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior through our reporting channels.

---

## Development Environment Setup

### 1. Prerequisites
- **Python**: 3.10, 3.11, 3.12, or 3.13.
- **C Compiler**: GCC (MinGW-w64 on Windows), Clang, or MSVC.
- **Git**: Latest release.

### 2. Clone and Setup Environment
```bash
git clone https://github.com/pen10plus/project-gama.git
cd project-gama

# Create and activate a virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

---

## Repository Architecture

The project consists of three tightly coupled layers:

```
├── engine/
│   ├── ast_engine/       # Stage 1: Docstring stripping, scoping, control-flow flattening, symbol mangling, string encryption
│   ├── native_crypto/    # Stage 2: Pure C99 ChaCha20 cipher, anti-debugging watchdogs, hardware fingerprinting
│   ├── crypto/           # Build-time key derivation (KDF)
│   └── pipeline/         # Nuitka compiler plugin injection & native build driver
├── examples/             # Verification sample applications
├── qa/                   # Adversarial benchmarks (CFG complexity expansion, Frida memory leak, latency)
├── tests/                # Regression tests (Equivalence, deep obfuscation, CLI stress, native crypto)
├── docs/                 # Architecture and security model specifications
└── protect_cli.py        # Single-command CLI orchestrator
```

---

## Testing & Quality Assurance

Every contribution must pass the comprehensive test suite and meet our zero-leakage security benchmarks before being merged.

### 1. Run Unit & Regression Tests (22 Tests)
```bash
python -m unittest discover tests
```

### 2. Compile & Run Native C Subsystems
On Windows (MinGW/Clang):
```bash
clang -O3 -Wall -Wextra tests/test_native_crypto.c \
  engine/native_crypto/chacha20.c \
  engine/native_crypto/anti_debug.c \
  engine/native_crypto/hw_digest.c \
  -o dist/test_native_crypto.exe -ladvapi32
./dist/test_native_crypto.exe
```

On Linux:
```bash
gcc -O3 -Wall -Wextra tests/test_native_crypto.c \
  engine/native_crypto/chacha20.c \
  engine/native_crypto/anti_debug.c \
  engine/native_crypto/hw_digest.c \
  -o dist/test_native_crypto
./dist/test_native_crypto
```

### 3. Run Adversarial Red-Team & Performance Benchmarks
```bash
# Verify intermediate script generation
python protect_cli.py --input examples/sample_app.py --preserve main

# 1. CFG Expansion benchmark (McCabe cyclomatic complexity target >= +400%)
python qa/redteam_ghidra.py examples/sample_app.py dist/sample_app_protected.py

# 2. Static entropy & memory leak audit (Zero sensitive tokens)
python qa/redteam_frida.py dist/sample_app_protected.py

# 3. Execution overhead latency check (< 150ms delta)
python qa/benchmark_suite.py examples/sample_app.py dist/sample_app_protected.py
```

---

## Code Style & Standards

- **Formatting & Linting**: We use [`ruff`](https://github.com/astral-sh/ruff) for rapid linting and formatting.
  ```bash
  ruff check .
  ruff format .
  ```
- **Type Annotations**: All new Python functions must include PEP 484 type hints.
- **Zero Runtime Dependencies**: The core AST transformation engine must remain dependency-free (`ast`, `hashlib`, `sys`, etc.). Do not introduce heavy external Python dependencies without maintainer approval.
- **C99 Standard**: All native C code in `engine/native_crypto/` must strictly comply with C99 standard and compile without warnings on `-Wall -Wextra -pedantic`.

---

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Adds a new feature or transformation pass.
- `fix:` Fixes a bug or equivalence edge case.
- `docs:` Documentation improvements.
- `test:` Adds or modifies unit / regression tests.
- `refactor:` Code reorganization that does not affect functionality.
- `perf:` Performance improvements.
- `chore:` Maintenance, CI configuration, or packaging updates.

Example:
```git
feat(mangler): add support for mangling structural pattern matching identifiers
```

---

## Submitting a Pull Request

1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feat/my-new-transform
   ```
2. **Commit** your changes with clear, semantic commit messages.
3. **Verify** that all tests and linting checks pass:
   ```bash
   ruff check .
   python -m unittest discover tests
   ```
4. **Push** to your fork:
   ```bash
   git push origin feat/my-new-transform
   ```
5. Open a **Pull Request** against the `main` branch with a clear summary of your changes.

---

## Reporting Security Vulnerabilities

Please **do not** open public GitHub issues for security vulnerabilities. Instead, refer to our [Security Policy](SECURITY.md) for coordinated disclosure procedures.
