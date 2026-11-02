# Mal-Veil (v2.0)

[![CI Pipeline](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![C](https://img.shields.io/badge/C-C99%20Standard-green.svg)](https://en.wikipedia.org/wiki/C99)
[![Compiler](https://img.shields.io/badge/Compiler-Nuitka%20%7C%20GCC%20%7C%20Clang-orange.svg)](https://nuitka.net/)
[![Security](https://img.shields.io/badge/Security-Defense--in--Depth-red.svg)](docs/SECURITY_MODEL.md)
[![Tests](https://img.shields.io/badge/Tests-22%2F22%20Passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Runtime%20Dependencies-Zero-success.svg)](#4-technology-stack)

A defense-in-depth code protection, obfuscation, and native binary hardening toolchain for Python applications. It transforms high-level Python source code into scrambled, anti-reverse-engineered native executables capable of resisting static disassembly (Ghidra, IDA Pro), dynamic binary instrumentation (Frida), and memory dumping attacks.

---

## Table of Contents
- [1. Executive Overview](#1-executive-overview)
- [2. System Architecture](#2-system-architecture)
- [3. Key Features](#3-key-features)
- [4. Technology Stack](#4-technology-stack)
- [5. Repository Layout](#5-repository-layout)
- [6. Prerequisites & Installation](#6-prerequisites--installation)
- [7. Usage Instructions](#7-usage-instructions)
- [8. Multi-Tier QA & Adversarial Benchmarks](#8-multi-tier-qa--adversarial-benchmarks)
- [9. Security Model & Threat Mitigation](#9-security-model--threat-mitigation)
- [10. Community & Contributing](#10-community--contributing)
- [11. License](#11-license)

---

## 1. Executive Overview

Standard Python packaging solutions (e.g., PyInstaller, standard PyArmor) pack Python bytecode into extractable archives or rely on heavy third-party cryptographic libraries that expose plaintext strings and symbols in memory through CPython API hooks (`PyUnicode_FromString`, `sys.settrace`, `gc.get_objects()`).

The **Hardened Protection Engine** resolves these vulnerabilities through a multi-tier pipeline:
1. **Source-to-Source AST Transformation**: Strips metadata/docstrings, hashes symbols using deterministic scope trees, flattens control flow into non-linear state-machine dispatch loops with volatile runtime opaque predicates, and deeply mangles proprietary class names, method names, parameters, and object attributes.
2. **String Literal & Print Statement Encryption**: Encrypts all string constants, print statements, and formatted string expressions (`f-strings`) into inline decryptor calls (`_0xdec(bytes, key)`), leaving zero plaintext strings in the source or binary.
3. **Native C99 Ephemeral Cryptography**: Implements an in-memory ChaCha20 stream cipher with in-place zeroization (`secure_zero_memory`), eliminating external Python crypto dependencies (e.g., OpenSSL/Rust bloat).
4. **Native Binary Compilation**: Binds Python logic with C anti-debugging watchdogs (`PEB`, hardware breakpoints `DR0`–`DR3`, Frida detection) and compiles to a stripped native binary via Nuitka.

---

## 2. System Architecture

### High-Level Workflow Pipeline

```
  +-----------------------+
  | Original Python Code  | (e.g. examples/sample_app.py)
  +-----------------------+
              │
              ▼ [STAGE 1: AST MUTATION & SANITIZATION]
  +-------------------------------------------------------------+
  |  • ASTSanitizer: Strip docstrings, comments, & PEP 484      |
  |  • ScopeAnalyzer: Hierarchical lexical scope boundary maps  |
  |  • ControlFlowFlattener: State-machine while dispatch loops |
  |  • SymbolMangler: Deeply hash classes, methods, params,     |
  |    attributes, and local variables to deterministic hex     |
  |  • StringEncryptor: Encrypt string constants, print calls,  |
  |    and f-strings into inline dynamic rolling stream ciphers |
  +-------------------------------------------------------------+
              │
              ▼ [STAGE 2: NATIVE C CRYPTOGRAPHY & COMPILER INJECTION]
  +-------------------------------------------------------------+
  |  • chacha20.c: Pure C99 RFC 7539 stream cipher              |
  |  • anti_debug.c: PEB, DR0-DR3, & Frida DBI detection        |
  |  • hw_digest.c: MachineGuid & binary code integrity hashing |
  |  • nuitka_plugin.py: C compiler injection & LTO flags       |
  +-------------------------------------------------------------+
              │
              ▼ [STAGE 3: COMPILATION & PACKAGING]
  +-------------------------------------------------------------+
  |  • Native C++ Code Generation & Scons Compilation           |
  |  • Link-Time Optimization & Symbol Stripping                |
  |  • Native Executable Assembly (.exe / ELF)                  |
  +-------------------------------------------------------------+
              │
              ▼
  +-------------------------------------------------------------+
  |  Standalone Hardened Native Binary Executable (5.17 MB)     |
  +-------------------------------------------------------------+
```

---

## 3. Key Features

- **String Literal & Print Statement Encryption**: All plaintext strings in code, `print(...)` statements, return values, dictionary keys, and `f-strings` are encrypted into inline decryptor calls (`_0xdec(bytes, key)`). Zero plaintext strings remain in the transformed AST or binary.
- **Deep Identifier & Symbol Mangling**: Completely mangles proprietary class names (`_0x...`), method names, function parameters, keyword call arguments, object attributes (`self._0x...`), and local variables while preserving Python built-in types, standard library methods, and configured entrypoints (`main`).
- **Non-Linear Control Flow Flattening (CFF)**: Function bodies are fragmented into basic blocks wrapped inside a randomized state-dispatcher loop, increasing cyclomatic complexity by over **+575%** to prevent linear decompilation.
- **Volatile Opaque Predicates**: Injects mathematical invariants evaluated against runtime properties (`len(__name__)`), preventing compiler de-flattening passes from optimizing dispatchers away.
- **Zero Python Cryptography Dependency**: Pure C99 ChaCha20 cipher eliminates the 50 MB OpenSSL/Rust footprint associated with standard Python cryptography packages.
- **Ephemeral In-Memory Decryption**: Decrypts payloads strictly on-demand into transient buffers and immediately shreds memory using dead-store-resistant zeroization (`memset_s` semantics).
- **Hardware-Bound & Code-Bound KDF**: Derives encryption keys from a composite digest of system hardware serials and the binary's `.text` section hash. Any binary tampering invalidates decryption keys automatically.
- **Active Anti-Debugging Watchdogs**: Continuously probes for interactive debuggers (`x64dbg`, `gdb`), CPU debug registers (`DR0`–`DR3`), and dynamic instrumentation agents (Frida).

---

## 4. Technology Stack

| Layer | Technologies & Standards | Purpose |
| :--- | :--- | :--- |
| **AST Transformation** | Python 3.10+ `ast`, `hashlib`, `asyncio` | High-level syntax parsing, deep mangling, string encryption, and code regeneration. |
| **Native Cryptography** | C99 (GCC, Clang, MSVC, Zig) | Low-level ChaCha20 stream cipher, memory shredding, and FNV-1a checksums. |
| **Security & Anti-Analysis**| Win32 APIs (`GetThreadContext`, `IsDebuggerPresent`, `RegOpenKeyExA`), Linux POSIX (`ptrace`, `/proc/self/status`) | Hardware breakpoint detection, PEB inspection, and anti-hooking. |
| **Compiler Backend** | Nuitka 4.3+, Scons | C++ SSA code generation, Link-Time Optimization (LTO), and standalone packaging. |
| **QA & Verification** | Python `unittest`, Frida, Headless Ghidra scripts | Equivalence verification, CFG entropy checks, and memory leak audits. |

---

## 5. Repository Layout

```text
gama-protect/
├── .github/
│   ├── workflows/                 # Multi-OS CI, CodeQL/Bandit security, Release packaging
│   ├── ISSUE_TEMPLATE/            # Structured bug report & feature request forms
│   └── PULL_REQUEST_TEMPLATE.md   # Standard pull request checklist
├── engine/
│   ├── ast_engine/
│   │   ├── sanitizer.py           # Strips docstrings, comments, & PEP 484 annotations
│   │   ├── scope_analyzer.py      # Lexical scope resolution & boundary identification
│   │   ├── mangler.py             # Scope-aware identifier hashing (classes, methods, attributes, params)
│   │   ├── flattener.py           # State-machine dispatcher & opaque predicates
│   │   └── string_encryptor.py    # String literal and print statement encryption
│   ├── native_crypto/
│   │   ├── chacha20.h / .c        # Pure C99 RFC 7539 ChaCha20 cipher & zeroization
│   │   ├── anti_debug.h / .c      # PEB, hardware breakpoint (DR0-DR3), & Frida watchdog
│   │   └── hw_digest.h / .c       # MachineGuid & code-integrity hash (FNV-1a / SHA-256)
│   ├── crypto/
│   │   └── kdf.py                 # Pure Python build-time ChaCha20 key derivation
│   └── pipeline/
│       ├── nuitka_plugin.py       # Custom Nuitka plugin injecting C crypto & watchdogs
│       └── compiler.py            # Hardened Nuitka build driver (LTO, strip, ASLR)
├── qa/
│   ├── benchmark_suite.py         # Startup latency & memory budget benchmarking
│   ├── redteam_frida.py           # Memory inspection & string leak audit simulation
│   └── redteam_ghidra.py          # CFG cyclomatic complexity & entropy analyzer
├── tests/
│   ├── test_ast_equivalence.py    # Base functional equivalence regression tests
│   ├── test_advanced_qa.py        # Advanced Python language features (async, kwargs, lambdas)
│   ├── test_cli_and_stress.py     # CLI stress, edge case, and syntax tests
│   ├── test_obfuscation_depth.py  # String encryption & deep mangling verification tests
│   └── test_native_crypto.c       # Native C subsystem integration test
├── examples/
│   └── sample_app.py              # Algorithmic pricing engine sample application
├── docs/
│   ├── ARCHITECTURE.md            # Technical architecture documentation
│   └── SECURITY_MODEL.md          # Threat model and STRIDE mitigation matrix
├── protect_cli.py                 # Unified single-command CLI orchestrator
├── pyproject.toml                 # Standard PEP 517/621 packaging metadata
├── setup.py                       # Legacy compatibility installation shim
├── MANIFEST.in                    # Source distribution package inclusions
├── LICENSE                        # MIT License
├── CONTRIBUTING.md                # Contributor guidelines and workflow
├── CODE_OF_CONDUCT.md             # Contributor Covenant v2.1
├── SECURITY.md                    # Coordinated vulnerability disclosure policy
├── CHANGELOG.md                   # Keep-a-Changelog release history
└── README.md                      # Comprehensive project documentation
```

---

## 6. Prerequisites & Installation

### Requirements
- **Python**: Version 3.10 or higher.
- **C Compiler**: GCC (MinGW-w64 on Windows), Clang, or MSVC.
- **Nuitka** (Optional, for native binary compilation): `pip install nuitka`

### Installation
You can install the package in editable development mode with optional development dependencies:
```bash
# Clone the repository
git clone https://github.com/pen10plus/project-gama.git
cd project-gama

# Install core CLI & package
pip install -e .

# Or install with developer tooling (ruff, pytest, mypy)
pip install -e ".[dev]"
```
After installation, you can invoke the CLI via `gama-protect` or `python protect_cli.py`.

---

## 7. Usage Instructions

### 7.1 Single-Command Source Protection (AST Layer)
Transform, sanitize, flatten, deeply mangle, and encrypt strings while verifying functional equivalence:
```bash
python protect_cli.py --input examples/sample_app.py --preserve main
```
*Output*: Generates `dist/sample_app_protected.py`.

### 7.2 CLI Options Reference
```text
options:
  -h, --help            Show this help message and exit
  --input INPUT, -i     Path to the Python script to protect (Required)
  --output-dir DIR, -o  Destination directory for output artifacts (default: dist)
  --salt SALT           Cryptographic salt for symbol hashing
  --preserve SYMBOLS    Comma-separated list of function/class names to preserve
  --no-flatten          Disable control flow flattening
  --no-mangle           Disable symbol mangling
  --no-strings          Disable string literal encryption
  --compile, -c         Compile directly to native standalone binary (.exe / ELF)
  --no-verify           Skip automated runtime equivalence verification
```

### 7.3 Native Standalone Compilation
Compile the hardened script into a native standalone executable:
```bash
python protect_cli.py --input examples/sample_app.py --compile --preserve main
```
*Output*: Produces a self-contained executable in `dist/sample_app_protected.dist/`.

---

## 8. Multi-Tier QA & Adversarial Benchmarks

The project includes an automated multi-tier QA test suite validating equivalence, performance, and adversarial resistance.

### Running Automated Test Suites (22 Tests)
```bash
# Run all unit, integration, stress, and obfuscation depth tests
python -m unittest discover tests
```

### Running Native C Integration Test
```bash
# Execute compiled native C test binary
./dist/test_native_crypto.exe
```

### Running Adversarial Red-Team & Performance Benchmarks
```bash
# 1. Performance & Latency Budget Benchmark (<150ms delta target)
python qa/benchmark_suite.py examples/sample_app.py dist/sample_app_protected.py

# 2. Control Flow Graph Complexity Growth (Target: >= 400% expansion)
python qa/redteam_ghidra.py examples/sample_app.py dist/sample_app_protected.py

# 3. Static Memory & String Leak Audit
python qa/redteam_frida.py dist/sample_app_protected.py
```

### Benchmark Results
- **Functional Equivalence**: 22 of 22 tests passed (100% execution parity).
- **String Leak Audit**: Zero plaintext strings, print statements, or proprietary names found.
- **CFG Complexity Expansion**: Original `4` $\to$ Protected `27` (**+575.0%** increase).
- **Execution Overhead**: **< 1 ms delta** (Target budget: $< 150\text{ ms}$).
- **Binary Footprint**: Standalone executable package size is **5.17 MB**.

---

## 9. Security Model & Threat Mitigation

| Threat Vector | Attack Mechanism | Engine Defense |
| :--- | :--- | :--- |
| **String & Asset Extraction** | Extracting API keys, print logs, and URLs from code. | **String Encryption**: Encrypts literals and f-strings into rolling XOR byte streams (`_0xdec`). |
| **Reverse Engineering Logic** | Reading class and method names in decompilers. | **Deep Identifier Mangling**: Proprietary classes, methods, parameters, and attributes are renamed to opaque hashes (`_0x...`). |
| **Static Decompilation** | Decompiling control structures with Ghidra/IDA. | **Non-Linear CFF**: Breaks linear flow into hashed state-machine dispatch loops with opaque predicates. |
| **Dynamic Memory Dumping** | Dumping strings and secrets from process memory. | **Ephemeral C Decryption**: Strings are decrypted on demand and immediately shredded via `secure_zero_memory()`. |
| **API Hooking / DBI** | Frida intercepting `PyUnicode_FromString`. | **Anti-Hooking Watchdog**: Probes loaded module tables for `frida-agent.dll` and executable memory hooks. |
| **Binary Patching** | NOPing license checks (`0x90` on `jz`/`jnz`). | **Code-Bound KDF**: SHA-256 hash of the `.text` section is bound to the key; patching 1 byte corrupts decryption. |
| **Interactive Debugging** | Stepping through code via x64dbg/GDB. | **PEB & Hardware BP Probing**: Active inspection of `BeingDebugged` and CPU registers `DR0`–`DR3`. |

For in-depth threat modeling and STRIDE analysis, refer to [**`docs/SECURITY_MODEL.md`**](docs/SECURITY_MODEL.md).

---

## 10. Community & Contributing

Contributions are welcome! Please review our community guidelines before opening an issue or pull request:
- **[Contributing Guide](CONTRIBUTING.md)**: Development setup, coding standards, and PR workflows.
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Community standards and enforcement policy (Contributor Covenant 2.1).
- **[Security Policy](SECURITY.md)**: Vulnerability disclosure and response expectations.
- **[Changelog](CHANGELOG.md)**: Historical release notes and version progression.

---

## 11. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete terms.
