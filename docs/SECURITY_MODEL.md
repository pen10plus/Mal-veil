# Python Hardened Protection Engine (v2.0): Security Model & Threat Matrix

## 1. Threat Landscape & Adversary Profile

We model an adversary with **unrestricted user-mode access** to the target workstation equipped with standard reverse-engineering toolkits:
- **Disassemblers / Decompilers**: Ghidra, IDA Pro, Binary Ninja, Cutter.
- **Dynamic Binary Instrumentation (DBI)**: Frida, Gum, Cheat Engine, Intel PIN.
- **Interactive Debuggers**: x64dbg, WinDbg, GDB.
- **Memory Forensics**: Process Hacker, ProcDump, Volatility.

---

## 2. STRIDE Threat Matrix & Mitigations

| Category | Threat Description | Naive Implementation Risk | Hardened Engine Mitigation |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Adversary spoofs client hardware ID (MAC/UUID). | Python `uuid.getnode()` monkeypatched in RAM. | Hardware digest queried directly in native C from `HKLM\SOFTWARE\Microsoft\Cryptography` or `/etc/machine-id`. |
| **Tampering** | Binary patching (flipping `jz` / `jnz` opcodes or inserting `0x90` NOPs). | License checks bypassed by editing binary file. | **Code-Bound KDF**: The SHA-256 hash of the binary code section is required for decryption; patching 1 byte ruins runtime decrypt. |
| **Repudiation** | Replay of intercepted license tokens. | Stolen license key unlocked on foreign machines. | Ephemeral challenge-response and hardware binding. |
| **Information Disclosure** | Memory scraping of decrypted strings and sensitive constants. | Strings remain allocated in Python heap garbage collector indefinitely. | **Ephemeral C Decryption**: Strings are decrypted on-demand and immediately zeroized using `secure_zero_memory()`. |
| **Denial of Service** | Process crash caused by invalid state dispatch. | Unhandled exceptions bubble up to console. | Opaque predicates guarantee valid execution while bewildering symbolic analysis engines. |
| **Elevation of Privilege** | Dynamic API hooking to hijack execution. | Frida hooks `PyUnicode_FromString` or native exports. | Active watchdog scans for `frida-agent.dll`, `frida-gadget.dll`, and `PAGE_EXECUTE_READWRITE` code trampolines. |

---

## 3. Anti-Analysis Layer Implementation

### 3.1 Process Environment Block (PEB) Inspection
```c
if (IsDebuggerPresent() || CheckRemoteDebuggerPresent(GetCurrentProcess(), &is_remote)) {
    exit(1);
}
```

### 3.2 Hardware Breakpoint Probing
Inspects CPU Debug Registers `DR0`–`DR3`:
```c
CONTEXT ctx;
ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
if (GetThreadContext(hThread, &ctx)) {
    if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3) {
        exit(1);
    }
}
```

### 3.3 Anti-DBI / Frida Signature Scanning
Probes loaded modules in the process virtual address space:
```c
if (GetModuleHandleA("frida-agent.dll") || GetModuleHandleA("frida-gadget.dll")) {
    exit(1);
}
```
