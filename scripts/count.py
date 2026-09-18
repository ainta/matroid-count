#!/usr/bin/env python3
"""Count all ten-element matroids from generated parents; no published totals as inputs.

Every answer is computed. Known values live only in validate.py. The
generator, independent-set counter, modular-cut worker and exact #SAT solver
write their own intermediate results for resumption and inspection.
"""

import argparse
import collections
import concurrent.futures
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from export_symmetry import export, partitions
from common import centralizer, physical_cpus
from run_symmetry import run_one

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
BIN = ROOT / "build"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def command(args, log):
    with log.open("w") as handle:
        subprocess.run(
            [str(x) for x in args],
            cwd=ROOT,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=True,
        )


def read(path):
    return json.loads(path.read_text())


def elementary(n):
    # Rank 2: a loop set and a partition of the remaining elements into >=2
    # nonempty parallel classes. Unlabeled classes are integer partitions.
    partition = [0] * (n + 1)
    partition[0] = 1
    for part in range(1, n + 1):
        for size in range(part, n + 1):
            partition[size] += partition[size - part]
    u2 = sum(partition[size] - 1 for size in range(2, n + 1))
    # Labeled rank 2: partition E union {*} into >=3 blocks; the block of *
    # marks the loops. Subtract partitions with 1 or 2 blocks: 2**n in total.
    stirling = [1] + [0] * (n + 1)
    for size in range(1, n + 2):
        stirling = [0] + [stirling[k - 1] + k * stirling[k] for k in range(1, n + 2)]
    return {0: (1, 1), 1: (n, 2**n - 1), 2: (u2, sum(stirling) - 2**n)}


def parent_moments(path, mode, paired, work, jobs, seconds):
    args = [
        sys.executable,
        "-S",
        SCRIPTS / "run_parents.py",
        path,
        "--mode",
        mode,
        "--workdir",
        work,
        "--jobs",
        jobs,
        "--seconds-per-class",
        seconds,
    ]
    if paired:
        args += ["--paired-coloop"]
    command(args, work.with_suffix(".log"))
    report = read(work / "result.json")
    manifest = read(work / "manifest.json")
    population = sum(1 for _ in path.open())
    if (
        report["status"] != "complete"
        or report["completed"] != population
        or report["scope"] != "all_parents"
    ):
        raise RuntimeError("Incomplete parent stage")
    if manifest["parents_sha256"] != sha(path) or manifest["worker_sha256"] != sha(
        BIN / "extension_worker"
    ):
        raise RuntimeError("Wrong parent provenance")
    rows = {}
    total = collections.Counter()
    with (work / "parents.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row["status"] != "complete":
                continue
            if row["row"] in rows and row["moments"] != rows[row["row"]]["moments"]:
                raise RuntimeError("Conflicting rows")
            rows[row["row"]] = row
    if set(rows) != set(range(population)):
        raise RuntimeError("Missing parent rows")
    for row in rows.values():
        total.update({k: int(v) for k, v in row["moments"].items()})
    if dict(total) != {k: int(v) for k, v in report["moments"].items()}:
        raise RuntimeError("Moment ledger mismatch")
    return {tuple(map(int, k.split("."))): v for k, v in total.items()}


def sat_count(item, seconds, directory):
    directory.mkdir(exist_ok=True, parents=True)
    row = run_one(item, seconds, directory)
    if row["status"] != "complete":
        return None
    log = (directory / (Path(item["file"]).stem + ".log")).read_text()
    exact = re.search(r"^c s exact arb int (\d+)\s*$", log, re.M)
    if not exact or exact.group(1) != row["count"] or "epsilon: 0 delta: 0" not in log:
        raise RuntimeError("Unverified #SAT log")
    return int(row["count"])


def symmetry(n, r, work, jobs, seconds):
    cnf = work / "cnf"
    cnf.mkdir(exist_ok=True)
    items = [
        export(n, r, t, cnf / ("_".join(map(str, t)) + ".cnf"))
        for t in partitions(n)
        if 1 not in t
    ]
    save(cnf / "manifest.json", items)

    def solve(item):
        # Split the known difficult double-transposition family from the start;
        # the cube selection is purely syntactic and never uses known answers.
        hard = n == 10 and r >= 4 and item["cycle_type"] == (2,) * 5
        value = None if hard else sat_count(item, seconds, work / "sat")
        if value is not None:
            return item["cycle_type"], value
        clauses = []
        for line in Path(item["file"]).read_text().splitlines():
            if line and line[0] not in "cp":
                clauses.append(tuple(map(int, line.split()[:-1])))
        freq = collections.Counter(abs(v) for clause in clauses for v in clause)
        variables = [
            v
            for v, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[
                : min(8, item["variables"])
            ]
        ]
        cubes = work / ("cubes_" + "_".join(map(str, item["cycle_type"])))
        cubes.mkdir(exist_ok=True)
        manifests = []
        for mask in range(1 << len(variables)):
            path = cubes / f"cube_{mask:05}.cnf"
            units = [v if mask >> i & 1 else -v for i, v in enumerate(variables)]
            with path.open("w") as target:
                target.write(
                    f"c t mc\np cnf {item['variables']} {len(clauses)+len(units)}\n"
                )
                for clause in clauses:
                    target.write(" ".join(map(str, clause)) + " 0\n")
                for lit in units:
                    target.write(f"{lit} 0\n")
            manifests.append(
                {
                    **item,
                    "cube": mask,
                    "file": str(path),
                    "units": units,
                    "clauses": len(clauses) + len(units),
                }
            )
        save(cubes / "manifest.json", manifests)
        save(
            cubes / "partition.json", {"variables": variables, "cubes": len(manifests)}
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            counts = list(
                pool.map(
                    lambda cube: sat_count(cube, seconds, cubes / "results"), manifests
                )
            )
        if any(value is None for value in counts):
            raise RuntimeError(
                "Unfinished symmetry cube; rerun with a larger --seconds limit"
            )
        return item["cycle_type"], sum(counts)

    # Direct instances are small, and one hard instance uses all allocated jobs.
    result = {}
    for item in items:
        key, value = solve(item)
        result[key] = value
        print(
            json.dumps(
                {"stage": "symmetry", "n": n, "r": r, "type": key, "fixed": str(value)}
            ),
            flush=True,
        )
    return result


def count_rank(n, r, parents, work, jobs, seconds, sparse=None):
    work.mkdir(exist_ok=True, parents=True)
    start = time.perf_counter()
    paired = sparse is not None
    if paired and (n, r) != (10, 5):
        raise ValueError("Sparse split configured only for 10,5")
    moments = collections.Counter(
        parent_moments(
            parents / f"n{n-1}_r{r}.txt",
            "nonsp" if paired else "all",
            paired,
            work / "parents",
            jobs,
            seconds,
        )
    )
    if not paired:
        moments.update(
            parent_moments(
                parents / f"n{n-1}_r{r-1}.txt",
                "coloop",
                False,
                work / "coloops",
                jobs,
                seconds,
            )
        )
    if set(moments) != set(partitions(n - 1)):
        raise RuntimeError("Missing moment cycle type")
    derangements = symmetry(n, r, work, jobs, seconds)
    sp = {}
    if sparse is not None:
        path = work / "sparse_terms.jsonl"
        with path.open("w") as out, path.with_suffix(".stderr").open("w") as error:
            subprocess.run(
                [str(BIN / "sparse_terms"), str(n), str(r)],
                stdout=out,
                stderr=error,
                check=True,
            )
        for line in path.read_text().splitlines():
            row = json.loads(line)
            key = tuple(row["cycle_type"])
            if key in sp or centralizer(key) != row["centralizer"]:
                raise RuntimeError("Invalid sparse term")
            sp[key] = int(row["fixed"])
        sp[(1,) * n] = int(sparse["labeled"])
        if set(sp) != set(partitions(n)):
            raise RuntimeError("Missing sparse fixed term")
        check = sum(math.factorial(n) // centralizer(t) * v for t, v in sp.items())
        if check != math.factorial(n) * int(sparse["unlabeled"]):
            raise RuntimeError("Sparse Burnside mismatch")
    fixed = {}
    bad = {}
    for lam in partitions(n):
        if 1 in lam:
            mu = list(lam)
            mu.remove(1)
            mu = tuple(mu)
            top = moments[mu] * centralizer(mu)
            value, remainder = divmod(top, math.factorial(n - 1))
            if remainder:
                raise RuntimeError("Nonintegral fixed count")
            if paired:
                bad[lam] = value
                value += sp[lam]
        else:
            value = derangements[lam]
            if paired:
                bad[lam] = value - sp[lam]
        if value < 0 or (paired and bad[lam] < 0):
            raise RuntimeError("Negative count")
        fixed[lam] = value
    numerator = sum(math.factorial(n) // centralizer(t) * v for t, v in fixed.items())
    unlabeled, remainder = divmod(numerator, math.factorial(n))
    if remainder:
        raise RuntimeError("Nonintegral Burnside result")
    report = {
        "status": "complete",
        "n": n,
        "r": r,
        "unlabeled": str(unlabeled),
        "labeled": str(fixed[(1,) * n]),
        "fixed_terms": {".".join(map(str, t)): str(v) for t, v in fixed.items()},
        "wall_seconds": time.perf_counter() - start,
    }
    if paired:
        bad_num = sum(math.factorial(n) // centralizer(t) * v for t, v in bad.items())
        if bad_num % math.factorial(n):
            raise RuntimeError("Nonintegral nonsp result")
        report.update(
            nonsp_unlabeled=str(bad_num // math.factorial(n)),
            sparse_unlabeled=sparse["unlabeled"],
            nonsp_fixed_terms={".".join(map(str, t)): str(v) for t, v in bad.items()},
        )
    save(work / "result.json", report)
    print(
        json.dumps({k: v for k, v in report.items() if "fixed_terms" not in k}),
        flush=True,
    )
    return report


def generate(work, jobs):
    parents = work / "parents"
    manifest = parents / "generation.json"
    if manifest.exists():
        data = read(manifest)
        if data["status"] != "complete" or data["all_ranklines_sha256"] != sha(
            parents / "all_ranklines.txt"
        ):
            raise RuntimeError("Generated parents corrupted")
        if data["generator_sha256"] != sha(ROOT / "vendor/matroid-generator/build/IC"):
            raise RuntimeError("Generator changed")
        for name, digest in data["rank_files_sha256"].items():
            if sha(parents / name) != digest:
                raise RuntimeError("Generated rank file corrupted")
    else:
        command(
            [
                sys.executable,
                "-S",
                SCRIPTS / "generate_parents.py",
                "--through",
                9,
                "--jobs",
                jobs,
                "--out",
                parents,
            ],
            work / "generation.log",
        )
    return parents


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workdir", required=True, type=Path)
    p.add_argument("--jobs", type=int, default=min(8, len(physical_cpus())))
    p.add_argument("--seconds", type=float, default=180)
    a = p.parse_args()
    if not 1 <= a.jobs <= len(physical_cpus()) or a.seconds <= 0:
        p.error("positive seconds and jobs within available physical cores required")
    work = a.workdir.resolve()
    work.mkdir(exist_ok=True, parents=True)
    start = time.perf_counter()
    parents = generate(work, a.jobs)
    print(
        json.dumps(
            {
                "stage": "parents_generated",
                "records": read(parents / "generation.json")["records"],
            }
        ),
        flush=True,
    )
    sparsework = work / "sparse10"
    command(
        [
            sys.executable,
            "-S",
            SCRIPTS / "count_sparse.py",
            10,
            5,
            "--jobs",
            a.jobs,
            "--seconds-per-root",
            a.seconds,
            "--workdir",
            sparsework,
        ],
        work / "sparse10.log",
    )
    sparse = read(sparsework / "result.json")
    if sparse["status"] != "complete":
        raise RuntimeError("Incomplete sparse count")
    reports = {}
    for rank in [3, 4, 5]:
        reports[rank] = count_rank(
            10,
            rank,
            parents,
            work / f"rank{rank}",
            a.jobs,
            a.seconds,
            sparse if rank == 5 else None,
        )
    table = {
        r: {"unlabeled": str(u), "labeled": str(l)}
        for r, (u, l) in elementary(10).items()
    }
    for r, row in reports.items():
        table[r] = {k: row[k] for k in ["unlabeled", "labeled"]}
    for r in range(5):
        table[10 - r] = dict(table[r])
    report = {
        "status": "complete",
        "n": 10,
        "scope": "all matroids, including loops, parallel elements, coloops and disconnected matroids",
        "catalogue_inputs": False,
        "published_totals_used_as_inputs": False,
        "all_unlabeled": str(sum(int(row["unlabeled"]) for row in table.values())),
        "all_labeled": str(sum(int(row["labeled"]) for row in table.values())),
        "by_rank": {str(r): table[r] for r in sorted(table)},
        "wall_seconds": time.perf_counter() - start,
        "generation": read(parents / "generation.json"),
    }
    save(work / "total.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
