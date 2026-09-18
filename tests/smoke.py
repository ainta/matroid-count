#!/usr/bin/env python3
"""Exercise known counts, the non-SP filter, resumption and invalid-input rejection."""

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import centralizer, physical_cpus
from count import count_rank, parent_moments
from export_symmetry import partitions


def run(*args, stdin=None):
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=ROOT,
        input=stdin,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def main():
    jobs = min(2, len(physical_cpus()))
    (ROOT / "runs").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="test-", dir=ROOT / "runs") as temporary:
        work = Path(temporary)
        parents = work / "parents"
        run(
            sys.executable,
            "scripts/generate_parents.py",
            "--through",
            8,
            "--jobs",
            jobs,
            "--out",
            parents,
        )
        run(
            sys.executable,
            "scripts/audit.py",
            parents / "all_ranklines.txt",
            "--out",
            work / "audit",
            "--jobs",
            jobs,
        )
        reports = {}
        for n, rank, expected in [(6, 3, 38), (7, 3, 108), (8, 4, 940)]:
            report = count_rank(n, rank, parents, work / f"count{n}", jobs, 60)
            assert int(report["unlabeled"]) == expected, report
            reports[n] = report

        # Repeat an already completed parent stage; require exact resumption.
        parent_moments(
            parents / "n5_r3.txt", "all", False, work / "count6/parents", jobs, 60
        )
        resumed = json.loads((work / "count6/parents/result.json").read_text())
        assert resumed["resumed"] == resumed["population"] == 13

        sparse = json.loads(
            run(
                sys.executable,
                "scripts/count_sparse.py",
                8,
                4,
                "--jobs",
                jobs,
                "--workdir",
                work / "sparse",
            )
        )
        assert sparse["status"] == "complete" and int(sparse["unlabeled"]) == 270
        sparse_fixed = {
            tuple(row["cycle_type"]): int(row["fixed"])
            for row in map(
                json.loads, run(ROOT / "build/sparse_terms", 8, 4).splitlines()
            )
        }
        sparse_fixed[(1,) * 8] = int(sparse["labeled"])
        bad = parent_moments(
            parents / "n7_r4.txt", "nonsp", True, work / "nonsp", jobs, 60
        )
        for mu in partitions(7):
            numerator = bad[mu] * centralizer(mu)
            assert numerator % math.factorial(7) == 0
            lam = tuple(sorted(mu + (1,)))
            full = int(reports[8]["fixed_terms"][".".join(map(str, lam))])
            assert numerator // math.factorial(7) == full - sparse_fixed[lam]

        for name, text in {
            "submodularity": "01111122\n",
            "empty_rank": "1\n",
            "shape": "011\n",
        }.items():
            path = work / (name + ".txt")
            path.write_text(text)
            check = subprocess.run(
                [str(ROOT / "build/rank_audit"), str(path), str(work / "bad.tsv"), "1"],
                capture_output=True,
            )
            assert check.returncode != 0, name
        duplicate = work / "duplicate.txt"
        duplicate.write_text("0101\n0011\n")
        check = subprocess.run(
            [
                sys.executable,
                "scripts/audit.py",
                str(duplicate),
                "--out",
                str(work / "duplicates"),
                "--jobs",
                "1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert check.returncode != 0 and "Isomorphic duplicate" in check.stderr
    print(
        "Passed: generation, rank axioms, isomorphism audit, known counts, "
        "sparse/non-sparse fixed counts, resumption and rejection controls."
    )


if __name__ == "__main__":
    main()
