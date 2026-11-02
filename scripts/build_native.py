"""
Cross-Platform Native C Subsystem Build Script
Compiles the RFC 7539 ChaCha20 cipher, anti-debug watchdogs, and hardware digest modules.
"""

import os
import platform
import shutil
import subprocess
import sys


def find_c_compiler():
    """Detects available C compiler on the host system."""
    for compiler in ["clang", "gcc", "cl"]:
        path = shutil.which(compiler)
        if path:
            return compiler, path
    return None, None


def build_native(output_dir: str = "dist"):
    os.makedirs(output_dir, exist_ok=True)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    native_dir = os.path.join(root, "engine", "native_crypto")
    test_src = os.path.join(root, "tests", "test_native_crypto.c")

    c_sources = [
        os.path.join(native_dir, "chacha20.c"),
        os.path.join(native_dir, "anti_debug.c"),
        os.path.join(native_dir, "hw_digest.c"),
    ]

    for src in c_sources + [test_src]:
        if not os.path.exists(src):
            print(f"[ERROR] Source file missing: {src}")
            return False

    compiler, comp_path = find_c_compiler()
    if not compiler:
        print("[WARN] No C compiler (clang, gcc, cl) detected on system PATH.")
        print("       Native C compilation skipped.")
        return False

    print(f"[*] Detected C compiler: {compiler} ({comp_path})")
    is_windows = platform.system() == "Windows"

    # Build 1: Test Integration Binary
    test_bin_name = "test_native_crypto.exe" if is_windows else "test_native_crypto"
    test_bin_path = os.path.join(output_dir, test_bin_name)

    if compiler in ["gcc", "clang"]:
        cmd_test = [
            comp_path,
            "-O3",
            "-Wall",
            "-Wextra",
            test_src,
            *c_sources,
            "-o",
            test_bin_path,
        ]
        if is_windows:
            cmd_test.extend(["-ladvapi32"])

        # Build 2: Shared Library
        lib_name = "native_security.dll" if is_windows else "libnative_security.so"
        lib_path = os.path.join(native_dir, lib_name)
        cmd_lib = [
            comp_path,
            "-O3",
            "-shared",
            "-fPIC",
            *c_sources,
            "-o",
            lib_path,
        ]
        if is_windows:
            cmd_lib.extend(["-ladvapi32"])

    elif compiler == "cl":
        # MSVC syntax
        cmd_test = [
            comp_path,
            "/O2",
            "/W3",
            f"/Fe:{test_bin_path}",
            test_src,
            *c_sources,
            "advapi32.lib"
        ]
        lib_name = "native_security.dll"
        lib_path = os.path.join(native_dir, lib_name)
        cmd_lib = [
            comp_path,
            "/O2",
            "/LD",
            f"/Fe:{lib_path}",
            *c_sources,
            "advapi32.lib"
        ]

    print(f"[+] Compiling native test runner: {test_bin_path}")
    res_test = subprocess.run(cmd_test, check=False)
    if res_test.returncode != 0:
        print("[FAIL] Compilation of native test runner failed!")
        return False

    print(f"[+] Compiling native shared library: {lib_path}")
    res_lib = subprocess.run(cmd_lib, check=False)
    if res_lib.returncode != 0:
        print("[FAIL] Compilation of native shared library failed!")
        return False

    print(f"[SUCCESS] Native C subsystems compiled successfully!")
    return True


if __name__ == "__main__":
    success = build_native()
    sys.exit(0 if success else 1)
