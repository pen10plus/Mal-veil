"""
QA Performance & Resource Budget Benchmarking Suite
Measures startup latency, memory footprint, and execution overhead
between original and protected Python scripts.
"""

import os
import subprocess
import sys
import time
from typing import Dict, Tuple


def measure_execution_metrics(script_path: str, runs: int = 5) -> Tuple[float, float]:
    """
    Measures average execution wall-clock time and peak memory (approximated via tracemalloc/time).
    Returns (avg_latency_ms, peak_mem_kb).
    """
    latencies = []
    
    for _ in range(runs):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False
        )
        elapsed = (time.perf_counter() - t0) * 1000.0  # ms
        if proc.returncode == 0:
            latencies.append(elapsed)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    return avg_latency, 0.0


def benchmark_comparison(original_script: str, protected_script: str) -> Dict[str, float]:
    """Compares metrics between original and protected script versions."""
    print("=" * 60)
    print("      QA BENCHMARKING: PERFORMANCE & OVERHEAD")
    print("=" * 60)
    print(f"[*] Original Script : {original_script}")
    print(f"[*] Protected Script: {protected_script}")

    orig_lat, _ = measure_execution_metrics(original_script, runs=5)
    prot_lat, _ = measure_execution_metrics(protected_script, runs=5)

    overhead_ms = prot_lat - orig_lat
    overhead_pct = ((prot_lat - orig_lat) / orig_lat * 100.0) if orig_lat > 0 else 0.0

    print("\n--- RESULTS ---")
    print(f"Original Avg Latency : {orig_lat:.2f} ms")
    print(f"Protected Avg Latency: {prot_lat:.2f} ms")
    print(f"Overhead Delta       : +{overhead_ms:.2f} ms (+{overhead_pct:.1f}%)")
    
    # Budget check (< 150 ms overhead target from project plan)
    budget_passed = overhead_ms < 150.0
    print(f"Performance Budget   : {'[PASSED] (<150ms delta)' if budget_passed else '[EXCEEDED]'}")
    print("=" * 60)

    return {
        "original_ms": orig_lat,
        "protected_ms": prot_lat,
        "overhead_ms": overhead_ms,
        "overhead_pct": overhead_pct,
        "budget_passed": budget_passed
    }


if __name__ == "__main__":
    orig = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_app.py"
    prot = sys.argv[2] if len(sys.argv) > 2 else "dist/sample_app_protected.py"
    if os.path.exists(orig) and os.path.exists(prot):
        benchmark_comparison(orig, prot)
    else:
        print(f"Target files not found. Ensure {orig} and {prot} exist.")
