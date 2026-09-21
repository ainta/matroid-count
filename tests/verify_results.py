#!/usr/bin/env python3
"""Ensure the result checker rejects incomplete and inconsistent evidence."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_results import read, verify_recorded, verify_run


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def reject(action, message):
    try:
        action()
    except ValueError:
        return
    raise AssertionError(message)


def main():
    original_counts = read(ROOT / "results/counts.json")
    original_terms = read(ROOT / "results/fixed_terms.json")
    verified = verify_recorded(ROOT / "results")
    cases = 0
    with tempfile.TemporaryDirectory(prefix="matroid-result-check-") as temporary:
        work = Path(temporary)
        # Each corruption represents a distinct failure in a submitted result.
        for failure in ["missing_type", "missing_nonsp_type", "nonintegral_sum",
                        "identity", "negative_sparse", "duality", "total", "missing_rank"]:
            counts, terms = copy.deepcopy(original_counts), copy.deepcopy(original_terms)
            table = terms["ranks"]["5"]["all"]
            if failure == "missing_type":
                del table["10"]
            elif failure == "missing_nonsp_type":
                del terms["ranks"]["5"]["non_sparse_paving"]["10"]
            elif failure == "nonintegral_sum":
                table["10"] = str(int(table["10"]) + 1)
            elif failure == "identity":
                counts["by_rank"]["5"]["labeled"] = str(int(counts["by_rank"]["5"]["labeled"]) + 1)
                counts["all_labeled"] = str(int(counts["all_labeled"]) + 1)
            elif failure == "negative_sparse":
                terms["ranks"]["5"]["non_sparse_paving"]["10"] = str(int(table["10"]) + 1)
            elif failure == "duality":
                counts["by_rank"]["6"]["unlabeled"] = "0"
            elif failure == "total":
                counts["all_unlabeled"] = str(int(counts["all_unlabeled"]) + 1)
            else:
                del counts["by_rank"]["10"]
            save(work / "counts.json", counts)
            save(work / "fixed_terms.json", terms)
            reject(lambda: verify_recorded(work), f"Accepted {failure}")
            cases += 1
        duplicate = work / "duplicate.json"
        duplicate.write_text('{"count": 1, "count": 2}\n')
        reject(lambda: read(duplicate), "Accepted duplicate JSON key")
        cases += 1

        # Minimal completed-run summaries exercise the comparison interface.
        run = work / "run"
        save(run / "total.json", original_counts)
        for r in [3, 4, 5]:
            report = {"status": "complete", "n": 10, "r": r,
                      **original_counts["by_rank"][str(r)],
                      "fixed_terms": original_terms["ranks"][str(r)]["all"]}
            if r == 5:
                report.update(original_counts["rank5_partition"])
                report["nonsp_fixed_terms"] = original_terms["ranks"]["5"]["non_sparse_paving"]
            save(run / f"rank{r}/result.json", report)
        save(run / "sparse10/result.json", {
            "status": "complete", "unlabeled": original_counts["rank5_partition"]["sparse_unlabeled"],
            "labeled": str(verified[3][(1,) * 10]),
        })
        verify_run(run, *verified)
        total = copy.deepcopy(original_counts)
        total["status"] = "partial"
        save(run / "total.json", total)
        reject(lambda: verify_run(run, *verified), "Accepted incomplete run")
        cases += 1
        save(run / "total.json", original_counts)
        rank5 = read(run / "rank5/result.json")
        rank5["fixed_terms"]["10"] = str(int(rank5["fixed_terms"]["10"]) + 1)
        save(run / "rank5/result.json", rank5)
        reject(lambda: verify_run(run, *verified), "Accepted altered run fixed count")
        cases += 1

        guide = work / "validation.md"
        guide.write_text((ROOT / "docs/validation.md").read_text().replace("11,692,562,643,915,909,321", "0"))
        require_changed = guide.read_text() != (ROOT / "docs/validation.md").read_text()
        assert require_changed, "Expected identity term missing from guide"
        check = subprocess.run([sys.executable, str(ROOT / "scripts/verify_results.py"),
                                "--check-table", str(guide)], capture_output=True, text=True)
        assert check.returncode != 0 and "out of date" in check.stderr
        cases += 1
    print(f"Passed: recorded results and run comparison; rejected {cases} inconsistent inputs.")


if __name__ == "__main__":
    main()
