#!/usr/bin/env python3
"""Check the recorded count, or compare it with a completed run."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate key in {path}: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique)


def integer(value):
    require(isinstance(value, str) and value.isdecimal(), "count is not a decimal string")
    return int(value)


def partitions(n, minimum=1):
    if n == 0:
        yield ()
    for part in range(minimum, n + 1):
        for tail in partitions(n - part, part):
            yield (part,) + tail


def cycle_key(parts):
    return ".".join(map(str, parts))


def centralizer(parts):
    return math.prod(length ** count * math.factorial(count)
                     for length, count in Counter(parts).items())


def verify(directory):
    total = read(directory / "result.json")
    require(total["n"] == 10, "wrong ground-set size")
    rows = total["by_rank"]
    require(set(rows) == {str(r) for r in range(11)}, "missing rank")
    counts = {
        r: {kind: integer(rows[str(r)][kind]) for kind in ("unlabeled", "labeled")}
        for r in range(11)
    }
    require(counts[0] == {"unlabeled": 1, "labeled": 1}, "wrong rank-zero count")
    require(counts[1] == {"unlabeled": 10, "labeled": 1023}, "wrong rank-one count")
    require(counts[2] == {"unlabeled": 128, "labeled": 677546}, "wrong rank-two count")
    require(counts[3]["unlabeled"] == 10037, "wrong published rank-three count")
    require(counts[4]["unlabeled"] == 4886380924, "wrong published rank-four count")
    for r in range(11):
        require(counts[r] == counts[10 - r], f"duality fails at rank {r}")
    for kind in ("unlabeled", "labeled"):
        require(sum(row[kind] for row in counts.values()) == integer(total[kind]),
                f"wrong {kind} total")

    types = {cycle_key(parts): parts for parts in partitions(10)}
    require(len(types) == 42, "wrong cycle types")
    fixed = {}
    for rank in (3, 4, 5):
        report = read(directory / f"rank{rank}/result.json")
        require((report["n"], report["rank"]) == (10, rank), f"wrong rank {rank} report")
        require(set(report["fixed_terms"]) == set(types), f"missing rank {rank} cycle type")
        require(all(integer(report[kind]) == counts[rank][kind]
                    for kind in ("unlabeled", "labeled")), f"rank {rank} mismatch")
        terms = {key: integer(value) for key, value in report["fixed_terms"].items()}
        identity = cycle_key((1,) * 10)
        require(terms[identity] == counts[rank]["labeled"], f"rank {rank} identity mismatch")
        require(all(value <= terms[identity] for value in terms.values()),
                f"rank {rank} fixed count exceeds identity")
        numerator = sum(math.factorial(10) // centralizer(parts) * terms[key]
                        for key, parts in types.items())
        quotient, remainder = divmod(numerator, math.factorial(10))
        require(remainder == 0 and quotient == counts[rank]["unlabeled"],
                f"rank {rank} Burnside sum fails")
        fixed[rank] = terms
    return counts, fixed


def verify_input_evidence(directory):
    generation = read(directory / "generation.json")
    audit = read(directory / "audit.json")
    comparison = read(directory / "catalogue-comparison.json")
    pinned = (ROOT / "vendor/matroid-generator/UPSTREAM_COMMIT").read_text().strip()
    require(generation["source_commit"] == pinned, "wrong parent generator source")
    require(generation["status"] == "complete", "parent generation is incomplete")
    require(generation["records"] == audit["records"] == 385370,
            "wrong generated catalogue size")
    require(generation["all_ranklines_sha256"] == audit["ranklines_sha256"],
            "audit used different parent data")
    require(audit["status"] == "passed" and audit["duplicates"] == 0
            and audit["dual_closure"], "parent audit failed")
    nine = sum(value for key, value in audit["counts"].items()
               if key.startswith("9,"))
    require(nine == 383172, "wrong nine-element catalogue size")
    require(comparison["status"] == "passed"
            and comparison["records_each"] == audit["records"]
            and comparison["full_canonical_rank_arrays_equal"]
            and comparison["canonical_files_sha256"]["generated"]
                == audit["canonical_sha256"]
            and comparison["missing_classes"] == 0
            and comparison["extra_classes"] == 0,
            "public catalogue comparison failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--run", type=Path, help="compare a completed scripts/count.py run")
    args = parser.parse_args()
    try:
        recorded = verify(args.results)
        verify_input_evidence(args.results)
        if args.run:
            fresh = verify(args.run)
            require(fresh == recorded, "completed run differs from recorded results")
        print("Verified all 42 cycle types at ranks 3–5, Burnside sums, duality, and totals.")
        print(f"Unlabeled: {sum(row['unlabeled'] for row in recorded[0].values()):,}")
        if args.run:
            print(f"Completed run matches: {args.run}")
    except (KeyError, OSError, ValueError) as error:
        parser.exit(1, f"Verification failed: {error}\n")


if __name__ == "__main__":
    main()
