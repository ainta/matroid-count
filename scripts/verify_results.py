#!/usr/bin/env python3
"""Check the recorded counts and Burnside sums, optionally against a completed run.

Uses Python's standard library only. This checks arithmetic and agreement of
recorded results; count.py regenerates the counting subproblems themselves.
"""

import argparse
import collections
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN = "<!-- BEGIN GENERATED BURNSIDE TABLE -->"
END = "<!-- END GENERATED BURNSIDE TABLE -->"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, f"Duplicate JSON key in {path}: {k}")
            result[k] = v
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def integer(value):
    require(type(value) is int or isinstance(value, str), "Count must be an integer")
    text = str(value)
    require(bool(text) and all("0" <= c <= "9" for c in text), "Invalid nonnegative count")
    return int(text)


def partitions(n, least=1):
    if n == 0:
        yield ()
    for k in range(least, n + 1):
        for tail in partitions(n - k, k):
            yield (k,) + tail


def cycle_key(parts):
    return ".".join(map(str, parts))


def centralizer(parts):
    return math.prod(k ** a * math.factorial(a)
                     for k, a in collections.Counter(parts).items())


def decode(table, types, context):
    require(isinstance(table, dict), f"Expected a fixed-count table: {context}")
    require(set(table) == {cycle_key(t) for t in types}, f"Wrong cycle types: {context}")
    return {t: integer(table[cycle_key(t)]) for t in types}


def burnside(table, n):
    factorial = math.factorial(n)
    numerator = sum(factorial // centralizer(t) * v for t, v in table.items())
    quotient, remainder = divmod(numerator, factorial)
    require(remainder == 0, "Nonintegral Burnside sum")
    return quotient, numerator


def verify_recorded(directory):
    counts = read(directory / "counts.json")
    terms = read(directory / "fixed_terms.json")
    n = 10
    require(counts["status"] == "complete" and counts["n"] == n, "Wrong count status or size")
    require(terms["n"] == n and terms["group"] == "S10", "Wrong symmetry group")
    require(set(counts["by_rank"]) == {str(r) for r in range(n + 1)}, "Missing rank")
    require(set(terms["ranks"]) == {"3", "4", "5"}, "Missing fixed-count rank")
    require(set(counts["rank5_partition"]) == {"sparse_unlabeled", "nonsp_unlabeled"},
            "Incorrect rank-five partition fields")
    types = list(partitions(n))
    require(sum(math.factorial(n) // centralizer(t) for t in types) == math.factorial(n),
            "Conjugacy classes do not cover S10")
    ranks = {r: {kind: integer(counts["by_rank"][str(r)][kind])
                 for kind in ["unlabeled", "labeled"]} for r in range(n + 1)}
    for r in ranks:
        require(ranks[r] == ranks[n - r], f"Duality mismatch at rank {r}")
    for kind in ["unlabeled", "labeled"]:
        require(sum(row[kind] for row in ranks.values()) == integer(counts[f"all_{kind}"]),
                f"Incorrect total: {kind}")
    tables = {}
    for r in [3, 4, 5]:
        table = decode(terms["ranks"][str(r)]["all"], types, f"rank {r}")
        require(table[(1,) * n] == ranks[r]["labeled"], f"Identity mismatch at rank {r}")
        require(all(v <= table[(1,) * n] for v in table.values()), "Fixed count exceeds labeled count")
        require(burnside(table, n)[0] == ranks[r]["unlabeled"], f"Burnside mismatch at rank {r}")
        tables[r] = table
    nonsp = decode(terms["ranks"]["5"]["non_sparse_paving"], types, "non-sparse paving")
    sparse = {t: tables[5][t] - nonsp[t] for t in types}
    require(all(v >= 0 for v in sparse.values()), "Negative sparse paving fixed count")
    for name, table in [("sparse", sparse), ("nonsp", nonsp)]:
        require(all(v <= table[(1,) * n] for v in table.values()),
                f"Fixed count exceeds labeled {name} count")
        expected = integer(counts["rank5_partition"][f"{name}_unlabeled"])
        require(burnside(table, n)[0] == expected, f"Incorrect rank-five {name} count")
    require(sum(integer(v) for v in counts["rank5_partition"].values()) == ranks[5]["unlabeled"],
            "Rank-five partition mismatch")
    return counts, tables, nonsp, sparse


def table_markdown(all_fixed, nonsp, sparse):
    def notation(t):
        return " ".join(str(k) if a == 1 else f"{k}<sup>{a}</sup>"
                        for k, a in sorted(collections.Counter(t).items()))
    lines = [BEGIN,
             "| Cycle type | Permutations of this type | All | Sparse paving | Non-sparse paving |",
             "|---|---:|---:|---:|---:|"]
    for t in sorted(all_fixed, key=lambda t: (-len(t), t)):
        values = [math.factorial(10) // centralizer(t), all_fixed[t], sparse[t], nonsp[t]]
        lines.append("| " + notation(t) + " | " + " | ".join(f"{v:,}" for v in values) + " |")
    lines.append(END)
    return "\n".join(lines)


def verify_run(work, counts, tables, nonsp, sparse):
    total = read(work / "total.json")
    require(total["status"] == "complete" and total["n"] == 10, "Run is incomplete")
    for kind in ["unlabeled", "labeled"]:
        require(integer(total[f"all_{kind}"]) == integer(counts[f"all_{kind}"]),
                f"Run total differs: {kind}")
    require(set(total["by_rank"]) == set(counts["by_rank"]), "Run is missing ranks")
    for r in counts["by_rank"]:
        for kind in ["unlabeled", "labeled"]:
            require(integer(total["by_rank"][r][kind]) == integer(counts["by_rank"][r][kind]),
                    f"Run differs at rank {r}: {kind}")
    for r in [3, 4, 5]:
        report = read(work / f"rank{r}" / "result.json")
        require(report["status"] == "complete" and (report["n"], report["r"]) == (10, r),
                f"Incomplete or wrong rank report: {r}")
        require(decode(report["fixed_terms"], tables[r], f"run rank {r}") == tables[r],
                f"Run fixed counts differ at rank {r}")
        for kind in ["unlabeled", "labeled"]:
            require(integer(report[kind]) == integer(counts["by_rank"][str(r)][kind]),
                    f"Rank report total differs: {r}")
        if r == 5:
            require(decode(report["nonsp_fixed_terms"], nonsp, "run non-sparse") == nonsp,
                    "Run non-sparse fixed counts differ")
            for name in ["sparse", "nonsp"]:
                require(integer(report[f"{name}_unlabeled"]) ==
                        integer(counts["rank5_partition"][f"{name}_unlabeled"]),
                        f"Run {name} rank-five total differs")
    report = read(work / "sparse10" / "result.json")
    require(report["status"] == "complete", "Incomplete sparse paving result")
    require(integer(report["labeled"]) == sparse[(1,) * 10] and
            integer(report["unlabeled"]) == integer(counts["rank5_partition"]["sparse_unlabeled"]),
            "Run sparse paving count differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--run", type=Path, help="Compare the summaries from a completed count.py run")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write-table", type=Path, help="Update the marked table in the validation guide")
    action.add_argument("--check-table", type=Path, help="Check that the guide matches the recorded data")
    args = parser.parse_args()
    try:
        counts, tables, nonsp, sparse = verify_recorded(args.results)
        document = args.write_table or args.check_table
        if document:
            text = document.read_text()
            require(text.count(BEGIN) == text.count(END) == 1, "Missing or duplicate table markers")
            begin, end = text.index(BEGIN), text.index(END) + len(END)
            expected = table_markdown(tables[5], nonsp, sparse)
            if args.write_table:
                document.write_text(text[:begin] + expected + text[end:])
            else:
                require(text[begin:end] == expected, "Validation table is out of date")
        if args.run:
            verify_run(args.run, counts, tables, nonsp, sparse)
        print("Passed: 126 fixed counts at ranks 3–5; rank-five sparse/non-sparse partition;")
        print("        Burnside sums, identity terms, duality, and totals over all 11 ranks.")
        print(f"Unlabeled: {integer(counts['all_unlabeled']):,}")
        print(f"Labeled:   {integer(counts['all_labeled']):,}")
        if args.run:
            print(f"Completed run matches: {args.run}")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"Verification failed: {error}\n")


if __name__ == "__main__":
    main()
