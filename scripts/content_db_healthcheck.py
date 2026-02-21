from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> int:
    print(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT)
    return int(proc.returncode)


def main() -> int:
    py = sys.executable
    steps: list[tuple[str, list[str]]] = [
        ("count-compare", [py, "scripts/compare_content_counts.py"]),
        ("query-regression", [py, "scripts/compare_catalog_queries.py"]),
        ("latency-benchmark", [py, "scripts/benchmark_catalog_latency.py"]),
    ]
    failed: list[str] = []
    for name, cmd in steps:
        code = _run(cmd)
        if code != 0:
            failed.append(f"{name}(exit={code})")
    if failed:
        print("healthcheck=FAIL")
        print("failed_steps=" + ", ".join(failed))
        return 1
    print("healthcheck=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
