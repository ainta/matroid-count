#!/usr/bin/env python3
"""Read progress without changing or blocking the count."""

import argparse
import json
from pathlib import Path
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("workdir", type=Path)
a = p.parse_args()
work = a.workdir


def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


final = read(work / "total.json")
if final:
    print(
        json.dumps(
            {
                k: final[k]
                for k in ["status", "all_unlabeled", "all_labeled", "wall_seconds"]
            },
            indent=2,
        )
    )
else:
    report = {"status": "incomplete", "checked_unix": time.time(), "stages": {}}
    report["stages"]["generation"] = read(work / "parents/generation.json") is not None
    sparse = read(work / "sparse10/result.json") or read(
        work / "sparse10/progress.json"
    )
    if sparse:
        report["stages"]["sparse"] = {
            k: v
            for k, v in sparse.items()
            if k in ["status", "completed_roots", "selected_roots", "wall_seconds"]
        }
    for rank in [3, 4, 5]:
        stage = work / f"rank{rank}"
        result = read(stage / "result.json")
        if result:
            report["stages"][str(rank)] = {
                k: result[k] for k in ["status", "unlabeled", "labeled", "wall_seconds"]
            }
            continue
        data = {}
        for name in ["parents", "coloops"]:
            progress = read(stage / name / "progress.json")
            if progress:
                data[name] = {
                    k: v
                    for k, v in progress.items()
                    if k
                    in [
                        "status",
                        "completed",
                        "selected",
                        "wall_seconds",
                        "updated_unix",
                    ]
                }
        records = [
            row
            for path in list(stage.glob("sat/*.json"))
            + list(stage.glob("cubes_*/results/*.json"))
            if (row := read(path)) is not None
        ]
        if records:
            data["sat_jobs"] = {
                "complete": sum(row["status"] == "complete" for row in records),
                "incomplete": sum(row["status"] != "complete" for row in records),
            }
        if data:
            report["stages"][str(rank)] = data
    print(json.dumps(report, indent=2))
