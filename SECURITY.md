# Security Policy

The **Python Hardened Protection Engine** community takes security, threat mitigation, and responsible disclosure seriously.

---

## Supported Versions

Only the latest major/minor release receives active security patches and bug fixes.

| Version | Supported          | Security Maintenance Status |
| :------ | :----------------- | :-------------------------- |
| 2.0.x   | :white_check_mark: | Current Active Release      |
| < 2.0   | :x:                | Deprecated / EOL            |

---

## Reporting a Vulnerability

If you discover a security vulnerability or bypass within the engine, please **do not open a public GitHub issue**.

### How to Disclose
1. **GitHub Private Vulnerability Reporting**: Use the [Security Advisory tab](https://github.com/pen10plus/project-gama/security/advisories/new) on GitHub.
2. **Email**: If private advisories are unavailable, email [security@projectgama.org](mailto:security@projectgama.org) with the subject:
   `[VULNERABILITY] <Component>: Brief description`

### Information to Include
- Detailed description of the vulnerability (AST leak, de-flattening attack, memory zeroization failure, or debugger bypass).
- Proof of Concept (PoC) script or reproduction steps.
- Compiler, operating system, and Python version used during testing.
- Proposed remediation or patch (if available).

### Response Timeline
- **Initial Acknowledgment**: Within **48 hours**.
- **Triage & Assessment**: Within **5 business days**.
- **Fix & Coordinated Release**: Within **14 business days** (depending on severity).

---

## Scope & Threat Model Expectations

The Hardened Protection Engine is a **defense-in-depth code protection, anti-reverse-engineering, and binary hardening toolchain**.

### In-Scope Vulnerabilities
- Plaintext string or symbol leaks in generated intermediate AST or compiled binaries.
- Algorithmic failure in the ChaCha20 cipher implementation or memory shredding (`secure_zero_memory`).
- Predictable or collision-prone identifier mangling that allows trivial symbol reconstruction.
- Control flow flattening regressions that cause execution desynchronization or semantic corruption.
- Buffer overflows or memory safety violations in native C subsystems (`chacha20.c`, `anti_debug.c`, `hw_digest.c`).

### Out-of-Scope (Expected Limitations)
- Kernel-level drivers / hypervisor-based debuggers (Ring 0) where the attacker controls CPU page tables and hardware virtualization.
- Side-channel physical hardware attacks (e.g. power analysis, cache timing on client silicon).
- Re-implementation of original source by complete manual dynamic tracing when execution output is intentionally visible to the end user.
