# Python Hardened Protection Engine (v2.0): Technical Architecture

## 1. System Overview

The Hardened Python Protection Engine transforms arbitrary Python 3.10+ source code into high-entropy, anti-reverse-engineered native binary executables. It combines **AST-level semantic obfuscation**, **in-memory C99 ephemeral cryptography**, and **custom compiler plugin injection** via Nuitka.

```
                           SYSTEM ARCHITECTURE FLOW
                           
  +-----------------------+
  | Original Python Code  |
  +-----------------------+
              │
              ▼ [AST Layer]
  +-------------------------------------------------------------+
  |  1. ASTSanitizer: Strip docstrings, comments, & PEP 484     |
  |  2. ScopeAnalyzer: Lexical scope resolution & boundary map   |
  |  3. ControlFlowFlattener: State-machine while dispatch      |
  |  4. SymbolMangler: Entropy hashing of local vars & functions|
  +-------------------------------------------------------------+
              │
              ▼ [Native Crypto & Plugin Layer]
  +-------------------------------------------------------------+
  |  1. chacha20.c: RFC 7539 C99 symmetric stream cipher       |
  |  2. anti_debug.c: PEB, HW Breakpoint, & Frida detection     |
  |  3. hw_digest.c: SMBIOS & code section integrity hash       |
  |  4. nuitka_plugin.py: C compiler injection & LTO flags      |
  +-------------------------------------------------------------+
              │
              ▼ [Build & Verification Layer]
  +-------------------------------------------------------------+
  |  1. Nuitka Native C++ Build (MSVC / GCC / Clang)            |
  |  2. Symbol Stripping (--strip) & Link-Time Optimization     |
  |  3. Automated Red-Team Validation (Frida & Ghidra tests)    |
  +-------------------------------------------------------------+
              │
              ▼
  +-------------------------------------------------------------+
  |  Hardened Standalone Native Binary Executable (.exe / ELF)  |
  +-------------------------------------------------------------+
```

---

## 2. Component Directory Structure

```text
abstract/
├── engine/
│   ├── ast_engine/
│   │   ├── sanitizer.py         # Docstring and annotation stripping
│   │   ├── scope_analyzer.py    # Lexical scope and symbol classification
│   │   ├── mangler.py           # Variable and helper function hashing
│   │   └── flattener.py         # State-machine control flow dispersion
│   ├── native_crypto/
│   │   ├── chacha20.h / .c      # Pure C99 ChaCha20 cipher & zeroization
│   │   ├── anti_debug.h / .c    # PEB, DR0-DR3, and Frida detection
│   │   └── hw_digest.h / .c     # MachineGuid & code-integrity hash
│   ├── crypto/
│   │   └── kdf.py               # Build-time key derivation & encryption
│   └── pipeline/
│       ├── nuitka_plugin.py     # Custom Nuitka C-injection plugin
│       └── compiler.py          # Native compiler driver
├── qa/
│   ├── benchmark_suite.py       # Latency and memory benchmarking
│   ├── redteam_frida.py         # Memory inspection & hooking simulator
│   └── redteam_ghidra.py        # CFG complexity & entropy validation
├── tests/
│   └── test_ast_equivalence.py  # 100% equivalence regression suite
├── examples/
│   └── sample_app.py            # High-value financial model sample
├── tasks/
│   └── todo.md                  # Milestone task tracking
├── protect_cli.py               # Unified build orchestrator
└── docs/
    ├── ARCHITECTURE.md          # Technical architecture
    └── SECURITY_MODEL.md        # Threat model & STRIDE matrix
```

---

## 3. Key Design Decisions

1. **Zero External Python Cryptography Dependencies**:
   - Compiling Python packages like `cryptography` introduces 50+ MB of OpenSSL/Rust bloat and exposes Python-level hooks.
   - We utilize a self-contained, 15 KB C99 ChaCha20 implementation compiled directly into native C space.

2. **Ephemeral In-Memory Decryption**:
   - Strings are decrypted into a transient C buffer, passed to CPython (`PyUnicode`), and immediately wiped from memory using `secure_zero_memory()` (`memset_s` semantics) to resist memory dumping.

3. **Multi-Factor Code-Bound KDF**:
   - Keys are derived from a composite digest:
     $$\text{Key} = \text{SHA256}(\text{Hardware GUID} \parallel \text{Executable .text Section Hash})$$
   - Any static binary patch (e.g., NOPing security checks) automatically corrupts the decryption key.
