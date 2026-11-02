"""
Native Compilation & Build Driver
Orchestrates Nuitka native compilation with custom hardening flags and plugins.
"""

import os
import shutil
import subprocess
import sys
from typing import List, Optional


class BuildDriver:
    """Invokes and configures Nuitka with Link-Time Optimization and stripping flags."""

    def __init__(self, output_dir: str = "dist"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.plugin_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "nuitka_plugin.py")
        )

    def is_nuitka_available(self) -> bool:
        """Checks if Nuitka is installed in the current Python environment."""
        try:
            res = subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    def build_native_binary(
        self,
        source_file: str,
        output_filename: Optional[str] = None,
        onefile: bool = True,
        lto: bool = True,
        strip: bool = True
    ) -> bool:
        """Executes the Nuitka build pipeline with native C injection."""
        if not self.is_nuitka_available():
            print("[WARN] Nuitka is not currently installed in this environment.")
            print("       To compile to native binary, run: pip install nuitka")
            return False

        cmd: List[str] = [
            sys.executable,
            "-m",
            "nuitka",
            "--standalone",
            f"--output-dir={self.output_dir}",
            "--remove-output",
            "--assume-yes-for-downloads",
            f"--user-plugin={self.plugin_path}"
        ]

        if onefile:
            cmd.append("--onefile")
        if lto:
            cmd.append("--lto=yes")
        # Stripping is enabled by default in Nuitka (use --unstripped to disable)

        if output_filename:
            cmd.append(f"--output-filename={output_filename}")

        cmd.append(os.path.abspath(source_file))

        print(f"[BUILD] Launching Nuitka build pipeline:")
        print(f"        Command: {' '.join(cmd)}")

        proc = subprocess.run(cmd, check=False)
        return proc.returncode == 0
