"""
Hardened Python Protection Engine CLI
Unified build orchestrator chaining AST sanitization, control-flow flattening,
deep symbol mangling, string literal encryption, and Nuitka native C-compilation.
"""

import argparse
import ast
import os
import subprocess
import sys
import time

from engine.ast_engine.sanitizer import sanitize_ast
from engine.ast_engine.flattener import flatten_control_flow
from engine.ast_engine.mangler import mangle_symbols
from engine.ast_engine.string_encryptor import encrypt_strings
from engine.pipeline.compiler import BuildDriver


def run_pipeline(
    input_file: str,
    output_dir: str = "dist",
    salt: str = "v2_hardened_pipeline",
    preserve_names: str = "main",
    flatten: bool = True,
    mangle: bool = True,
    encrypt_str: bool = True,
    compile_native: bool = False,
    verify_equivalence: bool = True
) -> str:
    """Executes the complete protection toolchain."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    protected_py_path = os.path.join(output_dir, f"{base_name}_protected.py")

    print("=" * 70)
    print("      PYTHON HARDENED PROTECTION TOOLCHAIN (v2.0)")
    print("=" * 70)
    print(f"[*] Target Source       : {input_file}")
    print(f"[*] Output Directory    : {output_dir}")
    print(f"[*] Control Flow Flatten: {'Enabled' if flatten else 'Disabled'}")
    print(f"[*] Symbol & Deep Mangle: {'Enabled' if mangle else 'Disabled'}")
    print(f"[*] String & Print Encr : {'Enabled' if encrypt_str else 'Disabled'}")
    print(f"[*] Preserve Symbols    : {preserve_names}")

    # Read original source
    with open(input_file, "r", encoding="utf-8") as f:
        original_source = f.read()

    # Step 1: AST Parsing
    print("\n[+] Stage 1: Parsing AST...")
    tree = ast.parse(original_source, filename=input_file)

    # Step 2: Sanitization (Docstrings, annotations, comments)
    print("[+] Stage 2: Stripping docstrings, type annotations, and comments...")
    tree = sanitize_ast(tree)

    # Step 3: Control Flow Flattening (Hashed state machines & opaque predicates)
    if flatten:
        print("[+] Stage 3: Applying non-linear hashed Control Flow Flattening...")
        tree = flatten_control_flow(tree)

    # Step 4: Symbol & Identifier Mangling (Classes, methods, parameters, attributes)
    if mangle:
        print("[+] Stage 4: Mangling classes, methods, parameters, and attributes...")
        preserved = {p.strip() for p in preserve_names.split(",") if p.strip()}
        tree = mangle_symbols(tree, salt=salt, preserve_names=preserved)

    # Step 5: String & Print Statement Encryption
    if encrypt_str:
        print("[+] Stage 5: Encrypting string literals and print statements into inline decryptors...")
        tree = encrypt_strings(tree)

    # Step 6: Unparse transformed AST
    print("[+] Stage 6: Unparsing intermediate protected Python code...")
    protected_code = ast.unparse(tree)

    with open(protected_py_path, "w", encoding="utf-8") as f:
        f.write(protected_code)
    print(f"[OK] Protected intermediate source written: {protected_py_path}")

    # Step 7: Functional Equivalence Verification
    if verify_equivalence:
        print("\n[+] Stage 7: Running functional equivalence verification...")
        t0 = time.perf_counter()
        orig_run = subprocess.run([sys.executable, input_file], capture_output=True, text=True, check=False)
        orig_time = time.perf_counter() - t0

        t1 = time.perf_counter()
        prot_run = subprocess.run([sys.executable, protected_py_path], capture_output=True, text=True, check=False)
        prot_time = time.perf_counter() - t1

        if orig_run.returncode != prot_run.returncode:
            print("[FAIL] Return code mismatch between original and protected script!")
            print(f"Original exit code: {orig_run.returncode}, Protected exit code: {prot_run.returncode}")
            print(f"Protected stderr:\n{prot_run.stderr}")
            sys.exit(1)
        if orig_run.stdout != prot_run.stdout:
            print("[FAIL] Output mismatch between original and protected script!")
            print(f"Original output:\n{orig_run.stdout}")
            print(f"Protected output:\n{prot_run.stdout}")
            sys.exit(1)

        print("[OK] Functional equivalence 100% VERIFIED!")
        print(f"     Original execution time : {orig_time*1000:.2f} ms")
        print(f"     Protected execution time: {prot_time*1000:.2f} ms")

    # Step 8: Native Nuitka Compilation
    if compile_native:
        print("\n[+] Stage 8: Compiling to native binary via Nuitka...")
        driver = BuildDriver(output_dir=output_dir)
        success = driver.build_native_binary(
            source_file=protected_py_path,
            output_filename=base_name,
            onefile=False,
            lto=False,
            strip=True
        )
        if success:
            print("[SUCCESS] Native standalone executable built successfully!")
        else:
            print("[WARN] Native build could not complete (Nuitka or C toolchain unavailable).")

    print("\n" + "=" * 70)
    print("      PROTECTION PIPELINE EXECUTION COMPLETED")
    print("=" * 70)
    return protected_py_path


def main():
    parser = argparse.ArgumentParser(
        description="Hardened Python Obfuscator & Native Hardening Pipeline"
    )
    parser.add_argument("--input", "-i", required=True, help="Path to Python script to protect")
    parser.add_argument("--output-dir", "-o", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--salt", default="v2_hardened_pipeline", help="Cryptographic salt for mangling")
    parser.add_argument("--preserve", default="main", help="Comma-separated symbols to preserve")
    parser.add_argument("--no-flatten", action="store_true", help="Disable control flow flattening")
    parser.add_argument("--no-mangle", action="store_true", help="Disable symbol mangling")
    parser.add_argument("--no-strings", action="store_true", help="Disable string literal encryption")
    parser.add_argument("--compile", "-c", action="store_true", help="Compile to standalone native binary")
    parser.add_argument("--no-verify", action="store_true", help="Skip runtime equivalence verification")

    args = parser.parse_args()

    run_pipeline(
        input_file=args.input,
        output_dir=args.output_dir,
        salt=args.salt,
        preserve_names=args.preserve,
        flatten=not args.no_flatten,
        mangle=not args.no_mangle,
        encrypt_str=not args.no_strings,
        compile_native=args.compile,
        verify_equivalence=not args.no_verify
    )


if __name__ == "__main__":
    main()
