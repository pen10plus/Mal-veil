# Changelog

All notable changes to the **Python Hardened Protection Engine** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-02

### Added
- **AST Transformation Pipeline**:
  - `ASTSanitizer`: Strips docstrings, comments, and PEP 484 type annotations from high-level Python source.
  - `ScopeAnalyzer`: Hierarchical lexical scope boundary maps preserving Python built-in namespaces while isolating inner scopes.
  - `ControlFlowFlattener`: Non-linear state-machine while dispatch loops with volatile runtime opaque predicates.
  - `SymbolMangler`: Deep scope-aware hashing of proprietary classes, methods, parameters, and object attributes.
  - `StringEncryptor`: Dynamic rolling stream encryption for string literals and print statements into inline decryptors (`_0xdec`).
- **Native C99 Ephemeral Cryptography**:
  - `chacha20.c / .h`: Pure RFC 7539 C99 symmetric stream cipher with in-place dead-store-resistant zeroization (`secure_zero_memory`).
  - `anti_debug.c / .h`: Active detection for Windows PEB `BeingDebugged`, CPU debug registers (`DR0`–`DR3`), and Frida/DBI runtime hooking.
  - `hw_digest.c / .h`: Hardware-bound fingerprinting (MachineGuid on Windows, machine-id on Linux) and `.text` code section integrity verification.
- **Compiler Plugin & Native Build Driver**:
  - `nuitka_plugin.py`: Custom compiler plugin injecting native C watchdogs and headers during C++ translation.
  - `compiler.py`: Automated build driver configuring Link-Time Optimization (LTO) and binary symbol stripping.
- **Unified CLI Tool**:
  - `protect_cli.py`: Single-command CLI orchestrating multi-stage protection, equivalence verification, and optional compilation.
- **Multi-Tier QA & Adversarial Suite**:
  - 22 comprehensive regression tests across AST equivalence, advanced language features, and stress testing.
  - Static cyclomatic complexity analyzer (`qa/redteam_ghidra.py`) proving +575.0% CFG expansion.
  - Frida DBI interception simulation (`qa/redteam_frida.py`) verifying 0 sensitive plaintext token leaks.
  - Latency overhead benchmark suite (`qa/benchmark_suite.py`) confirming < 1ms overhead delta.
- **Open Source Infrastructure**:
  - Comprehensive GitHub Actions CI/CD matrix for Linux, macOS, and Windows across Python 3.10–3.13.
  - Issue templates, pull request template, security policy, and contributing guidelines.
