#!/usr/bin/env python3
"""Published numbers are test expectations only, never production inputs.

Mayhew--Royle, Matroids with nine elements, Table 1:
https://arxiv.org/pdf/math/0702316
Joswig--Schroeter, Matroids from hypersimplex splits, Table 1:
https://doi.org/10.1016/j.jcta.2017.05.001
The latter attributes the 10-element rank-4 enumeration to Matsumoto et al.
"""

import argparse
import collections
import json
from pathlib import Path
from count import ROOT, count_rank, elementary, read, save

EXPECTED = {
    0: [1],
    1: [1, 1],
    2: [1, 2, 1],
    3: [1, 3, 3, 1],
    4: [1, 4, 7, 4, 1],
    5: [1, 5, 13, 13, 5, 1],
    6: [1, 6, 23, 38, 23, 6, 1],
    7: [1, 7, 37, 108, 108, 37, 7, 1],
    8: [1, 8, 58, 325, 940, 325, 58, 8, 1],
    9: [1, 9, 87, 1275, 190214, 190214, 1275, 87, 9, 1],
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parents", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--jobs", type=int, default=32)
    p.add_argument("--ten-run", type=Path)
    a = p.parse_args()
    a.parents = a.parents.resolve()
    a.out = a.out.resolve()
    a.out.mkdir(exist_ok=True, parents=True)
    counts = collections.Counter()
    for line in (a.parents / "all_ranklines.txt").open():
        line = line.strip()
        n = len(line).bit_length() - 1
        r = int(line[-1])
        counts[n, r] += 1
    for n, expected in EXPECTED.items():
        for r, total in enumerate(expected):
            if counts[n, r] != total:
                raise RuntimeError(
                    f"Published catalogue count mismatch {(n,r)}: {counts[n,r]} != {total}"
                )
    cases = []
    for n in range(4, 10):
        for r, (u, l) in elementary(n).items():
            if u != EXPECTED[n][r]:
                raise RuntimeError("Elementary formula mismatch")
        # Exercise the aggregate counting worker separately from the generator.
        for r in range(3, n // 2 + 1):
            report = count_rank(n, r, a.parents, a.out / f"n{n}_r{r}", a.jobs, 180)
            if int(report["unlabeled"]) != EXPECTED[n][r]:
                raise RuntimeError(f"Aggregate count mismatch {(n,r)}")
            cases.append(
                {
                    "n": n,
                    "r": r,
                    "expected": EXPECTED[n][r],
                    "computed": report["unlabeled"],
                }
            )
    if a.ten_run:
        report = read(a.ten_run / "total.json")
        for r, expected in [(0, 1), (1, 10), (2, 128), (3, 10037), (4, 4886380924)]:
            if int(report["by_rank"][str(r)]["unlabeled"]) != expected:
                raise RuntimeError(f"Ten-element benchmark failed, rank {r}")
            cases.append(
                {
                    "n": 10,
                    "r": r,
                    "expected": expected,
                    "computed": report["by_rank"][str(r)]["unlabeled"],
                }
            )
    result = {
        "status": "passed",
        "published_generation_cells_checked": sum(len(v) for v in EXPECTED.values()),
        "generated_total_by_n": {
            str(n): sum(counts[n, r] for r in range(n + 1)) for n in EXPECTED
        },
        "aggregate_cases": cases,
        "sources": [
            "https://arxiv.org/pdf/math/0702316",
            "https://doi.org/10.1016/j.jcta.2017.05.001",
        ],
    }
    save(a.out / "public_validation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
