#!/usr/bin/env python3
"""Compare full canonical rank arrays, never hashes alone."""

import collections
import argparse
import hashlib
import json
import math
from pathlib import Path


def load(path):
    by_key = {}
    counts = collections.Counter()
    labeled = collections.Counter()
    dual_checks = 0
    with path.open() as source:
        for line in source:
            row, n, r, aut, canonical, dual = line.rstrip("\n").split("\t")
            row, n, r, aut = map(int, (row, n, r, aut))
            if canonical in by_key:
                raise RuntimeError(
                    f"Isomorphic duplicates: {path} rows {row}, {by_key[canonical][0]}"
                )
            by_key[canonical] = (row, n, r, aut, dual)
            counts[f"{n},{r}"] += 1
            labeled[f"{n},{r}"] += math.factorial(n) // aut
    for canonical, (row, n, r, aut, dual) in by_key.items():
        if dual not in by_key:
            raise RuntimeError(f"Missing dual: {path} row {row}")
        match = by_key[dual]
        if match[1:4] != (n, n - r, aut) or match[4] != canonical:
            raise RuntimeError("Duality inconsistency")
        dual_checks += 1
    return by_key, dict(counts), dict(labeled), dual_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generated, gcounts, glabels, gduals = load(args.generated)
    reference, rcounts, rlabels, rduals = load(args.reference)
    missing = reference.keys() - generated.keys()
    extra = generated.keys() - reference.keys()
    if missing or extra:
        raise RuntimeError(
            f"Class mismatch: {len(missing)} missing, {len(extra)} extra"
        )
    if gcounts != rcounts or glabels != rlabels:
        raise RuntimeError("Count mismatch")
    for key, row in reference.items():
        if generated[key][1:4] != row[1:4]:
            raise RuntimeError("Nauty group comparison failed")
    report = {
        "status": "passed",
        "records_each": len(generated),
        "full_canonical_rank_arrays_equal": True,
        "isomorphic_duplicates_each": 0,
        "missing_classes": 0,
        "extra_classes": 0,
        "duality_checks": {"generated": gduals, "zenodo": rduals},
        "counts_by_size_rank": gcounts,
        "labeled_by_size_rank": glabels,
        "canonical_files_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in [
                ("generated", args.generated),
                ("zenodo", args.reference),
            ]
        },
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ["counts_by_size_rank", "labeled_by_size_rank"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
