#!/usr/bin/env python3
"""Generate all matroids through nine elements from the empty matroid.

No catalogue or expected count is read. The pinned independent IC generator
returns bases in colex order; ranks are reconstructed by subset dynamic
programming, and the higher ranks follow by duality.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import time

ROOT = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--through", type=int, default=9, choices=range(1, 10))
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--out", type=Path, default=ROOT / "generated")
    a = p.parse_args()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    generator = ROOT / "vendor/matroid-generator/build/IC"
    pin = generator.parents[1] / "UPSTREAM_COMMIT"
    commit = (
        pin.read_text().strip()
        if pin.exists()
        else subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=generator.parents[1], text=True
        ).strip()
    )
    manifest = {
        "source_commit": commit,
        "generator_sha256": hashlib.sha256(generator.read_bytes()).hexdigest(),
        "catalogue_input": False,
        "runs": [],
    }
    started = time.perf_counter()
    complete = []
    records = 1
    for n in range(1, a.through + 1):
        for r in range(n // 2 + 1):
            colex = a.out / f"n{n}_r{r}.colex"
            begin = time.perf_counter()
            with colex.open("w") as out:
                subprocess.run(
                    [str(generator), str(r), str(n), str(a.jobs)],
                    stdout=out,
                    check=True,
                )
            elapsed = time.perf_counter() - begin
            rankpath = a.out / f"n{n}_r{r}.txt"
            dualpath = a.out / (
                f"n{n}_r{n-r}.txt" if 2 * r != n else f"n{n}_r{r}.dual.txt"
            )
            count = int(
                subprocess.check_output(
                    [
                        str(ROOT / "build/colex_to_rank"),
                        str(n),
                        str(r),
                        str(colex),
                        str(rankpath),
                        str(dualpath),
                    ],
                    text=True,
                )
            )
            complete.append(rankpath)
            records += count
            if 2 * r != n:
                complete.append(dualpath)
                records += count
            item = {
                "n": n,
                "r": r,
                "count": count,
                "generation_seconds": elapsed,
                "colex_sha256": hashlib.sha256(colex.read_bytes()).hexdigest(),
            }
            manifest["runs"].append(item)
            print(json.dumps(item), flush=True)
    path = a.out / "all_ranklines.txt"
    with path.open("wb") as target:
        target.write(b"0\n")
        for part in complete:
            with part.open("rb") as source:
                shutil.copyfileobj(source, target)
    manifest["rank_files_sha256"] = {
        part.name: hashlib.sha256(part.read_bytes()).hexdigest() for part in complete
    }
    manifest.update(
        status="complete",
        records=records,
        wall_seconds=time.perf_counter() - started,
        all_ranklines_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    (a.out / "generation.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
