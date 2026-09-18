#!/usr/bin/env python3
"""Audit generated rank functions, uniqueness and dual closure without reference data."""

import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ranklines", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=32)
    a = p.parse_args()
    a.out.mkdir(exist_ok=True, parents=True)
    start = time.perf_counter()
    table = a.out / "canonical.tsv"
    with (a.out / "axioms.json").open("w") as log:
        subprocess.run(
            [str(ROOT / "build/rank_audit"), str(a.ranklines), str(table), str(a.jobs)],
            stderr=log,
            check=True,
        )
    classes = {}
    counts = collections.Counter()
    for line in table.open():
        row, n, r, aut, key, dual = line.rstrip("\n").split("\t")
        if key in classes:
            raise RuntimeError("Isomorphic duplicate in generated catalogue")
        classes[key] = (int(n), int(r), int(aut), dual)
        counts[f"{n},{r}"] += 1
    for key, (n, r, aut, dual) in classes.items():
        if classes.get(dual) != (n, n - r, aut, key):
            raise RuntimeError("Dual closure failed")
    result = {
        "status": "passed",
        "records": len(classes),
        "duplicates": 0,
        "dual_closure": True,
        "axiom_checks": json.loads((a.out / "axioms.json").read_text()),
        "counts": dict(counts),
        "ranklines_sha256": hashlib.sha256(a.ranklines.read_bytes()).hexdigest(),
        "seconds": time.perf_counter() - start,
    }
    (a.out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "counts"}, indent=2))


if __name__ == "__main__":
    main()
