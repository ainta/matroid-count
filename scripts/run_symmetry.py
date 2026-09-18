#!/usr/bin/env python3
"""Bounded deterministic #SAT jobs; incomplete runs never acquire a count."""

import argparse
import concurrent.futures
import json
import hashlib
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent


def run_one(item, seconds, out):
    path = Path(item["file"])
    fingerprint = {
        "cnf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "solver_sha256": hashlib.sha256((ROOT / "deps/ganak").read_bytes()).hexdigest(),
    }
    log = out / (path.stem + ".log")
    target = out / (path.stem + ".json")
    if target.exists():
        prior = json.loads(target.read_text())
        if prior["status"] == "complete" and all(
            prior.get(k) == v for k, v in fingerprint.items()
        ):
            return prior
    start = time.perf_counter()
    with log.open("w") as handle:
        try:
            completed = subprocess.run(
                [
                    str(ROOT / "deps/ganak"),
                    "--prob",
                    "0",
                    "--verb",
                    "0",
                    "--fast",
                    "--maxcache",
                    "1024",
                    str(path),
                ],
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=seconds,
            )
            status = "complete" if completed.returncode == 0 else "error"
        except subprocess.TimeoutExpired:
            status = "timeout"
    text = log.read_text()
    match = re.search(r"^c s exact arb int (\d+)\s*$", text, re.M)
    if status == "complete" and (not match or "epsilon: 0 delta: 0" not in text):
        status = "error"
    report = {
        **item,
        **fingerprint,
        "status": status,
        "seconds": time.perf_counter() - start,
        "deterministic": True,
    }
    if status == "complete":
        report["count"] = match.group(1)
    target.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=5)
    p.add_argument("--jobs", type=int, default=8)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = json.loads((a.directory / "manifest.json").read_text())
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = [pool.submit(run_one, row, a.seconds, a.out) for row in rows]
        result = []
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            result.append(row)
            print(json.dumps(row), flush=True)
    (a.out / "summary.json").write_text(
        json.dumps(
            {"wall_seconds": time.perf_counter() - started, "rows": result}, indent=2
        )
        + "\n"
    )
