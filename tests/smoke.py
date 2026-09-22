#!/usr/bin/env python3
"""Generate small parents and reproduce published matroid counts."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    completed = subprocess.run(
        [str(arg) for arg in args], cwd=ROOT, capture_output=True, text=True,
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout + completed.stderr)
    return completed.stdout


def main():
    jobs = min(2, os.cpu_count() or 1)
    (ROOT / "runs").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="test-", dir=ROOT / "runs") as temporary:
        work = Path(temporary)
        parents = work / "parents"
        run(sys.executable, "scripts/generate_parents.py", "--through", 8,
            "--jobs", jobs, "--out", parents)
        run(sys.executable, "scripts/audit.py", parents / "all_ranklines.txt",
            "--out", work / "audit", "--jobs", jobs)
        for n, rank, expected in [(6, 3, 38), (7, 3, 108),
                                   (8, 4, 940), (9, 4, 190214)]:
            output = work / f"n{n}_r{rank}"
            run(sys.executable, "-S", "scripts/count.py", "--n", n,
                "--rank", rank, "--parents", parents, "--workdir", output,
                "--jobs", jobs)
            actual = int(json.loads((output / "result.json").read_text())["unlabeled"])
            if actual != expected:
                raise AssertionError(f"n={n}, rank={rank}: {actual} != {expected}")
    print("Passed: parent generation, independent audit, and four published rank counts.")


if __name__ == "__main__":
    main()
