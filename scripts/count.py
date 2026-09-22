#!/usr/bin/env python3
"""Count rank-r matroids from rank lines for the (n-1)-element parents."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import math
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent


def partitions(n, minimum=1):
    if n == 0:
        yield ()
    for k in range(minimum, n + 1):
        for tail in partitions(n - k, k):
            yield (k,) + tail


def centralizer(parts):
    result = 1
    for length, count in Counter(parts).items():
        result *= length**count * math.factorial(count)
    return result


def key(parts):
    return ".".join(map(str, parts))


def parent_moments(path, mode, paired, jobs, seconds, worker):
    lines = path.read_text().splitlines()
    tasks = queue.Queue()
    for first in range(0, len(lines), 8):
        tasks.put((first, lines[first:first + 8]))
    done = 0
    lock = threading.Lock()
    stopped = threading.Event()
    started = time.perf_counter()

    def run_worker():
        nonlocal done
        process = subprocess.Popen(
            [str(worker), mode, str(seconds), "32768", str(int(paired))],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
        )
        totals = Counter()
        local_row = 0
        try:
            while not stopped.is_set():
                try:
                    _, batch = tasks.get_nowait()
                except queue.Empty:
                    break
                for line in batch:
                    process.stdin.write(line + "\n")
                    process.stdin.flush()
                    raw = process.stdout.readline()
                    if not raw:
                        raise RuntimeError(f"worker exited before row {local_row}")
                    item = json.loads(raw)
                    if item["row"] != local_row or item["status"] != "complete":
                        raise RuntimeError(f"incomplete parent: {item}")
                    totals.update({t: int(v) for t, v in item["moments"].items()})
                    local_row += 1
                with lock:
                    done += len(batch)
                    if done % 10000 < len(batch) or done == len(lines):
                        print(json.dumps({
                            "parent_file": str(path), "completed": done,
                            "total": len(lines),
                            "seconds": round(time.perf_counter() - started, 1),
                        }), file=sys.stderr, flush=True)
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError("worker exited with an error")
            return totals
        except BaseException:
            stopped.set()
            if process.poll() is None:
                process.terminate()
                process.wait()
            raise

    with ThreadPoolExecutor(max_workers=min(jobs, max(1, tasks.qsize()))) as pool:
        totals = Counter()
        for part in pool.map(lambda _: run_worker(), range(min(jobs, max(1, tasks.qsize())))):
            totals.update(part)
    if done != len(lines):
        raise RuntimeError("missing parent rows")
    return totals


def basis_formula(n, rank, parts, path):
    blocks = [sum(1 << i for i in c)
              for c in itertools.combinations(range(n), rank)]
    index = {block: i for i, block in enumerate(blocks)}
    permutation = list(range(n))
    offset = 0
    for length in parts:
        for i in range(length):
            permutation[offset + i] = offset + (i + 1) % length
        offset += length

    def image(block):
        return sum(1 << permutation[i] for i in range(n) if block >> i & 1)

    orbit = [-1] * len(blocks)
    variables = 0
    for i, block in enumerate(blocks):
        if orbit[i] >= 0:
            continue
        variables += 1
        current = block
        while orbit[index[current]] < 0:
            orbit[index[current]] = variables
            current = image(current)
    clauses = {tuple(range(1, variables + 1))}
    for i, left_block in enumerate(blocks):
        for j, right_block in enumerate(blocks):
            left = left_block & ~right_block
            right = right_block & ~left_block
            while left:
                element = left & -left
                left -= element
                clause = {-orbit[i], -orbit[j]}
                scan = right
                while scan:
                    replacement = scan & -scan
                    scan -= replacement
                    clause.add(orbit[index[(left_block ^ element) | replacement]])
                if not any(-literal in clause for literal in clause):
                    clauses.add(tuple(sorted(clause)))
    clauses = sorted(clauses)
    write_formula(path, variables, clauses)
    return variables, clauses


def write_formula(path, variables, clauses, units=()):
    with path.open("w") as out:
        out.write(f"c t mc\np cnf {variables} {len(clauses) + len(units)}\n")
        for clause in clauses:
            out.write(" ".join(map(str, clause)) + " 0\n")
        for literal in units:
            out.write(f"{literal} 0\n")


def exact_sat(solver, path, seconds):
    try:
        result = subprocess.run(
            [str(solver), "--prob", "0", "--verb", "0", "--fast",
             "--maxcache", "1024", str(path)],
            capture_output=True, text=True, timeout=seconds,
        )
    except subprocess.TimeoutExpired:
        return None
    match = re.search(r"^c s exact arb int (\d+)\s*$", result.stdout, re.M)
    if result.returncode or not match or "epsilon: 0 delta: 0" not in result.stdout:
        raise RuntimeError(f"solver failed on {path}")
    return int(match.group(1))


def fixed_without_point(n, rank, parts, work, jobs, seconds, solver):
    name = "_".join(map(str, parts))
    path = work / f"{name}.cnf"
    variables, clauses = basis_formula(n, rank, parts, path)
    hard = n == 10 and rank >= 4 and parts == (2,) * 5
    value = None if hard else exact_sat(solver, path, seconds)
    if value is not None:
        return value
    frequency = Counter(abs(v) for clause in clauses for v in clause)
    chosen = [v for v, _ in sorted(
        frequency.items(), key=lambda item: (-item[1], item[0])
    )[:min(8, variables)]]
    cubes = work / name
    cubes.mkdir(exist_ok=True)

    def solve_cube(mask):
        units = [v if mask >> i & 1 else -v for i, v in enumerate(chosen)]
        cube = cubes / f"{mask:05}.cnf"
        write_formula(cube, variables, clauses, units)
        count = exact_sat(solver, cube, seconds)
        if count is None:
            raise RuntimeError(f"unfinished symmetry cube {parts}, {mask}")
        return count

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return sum(pool.map(solve_cube, range(1 << len(chosen))))


def count_rank(n, rank, parents, work, jobs, seconds, worker, solver):
    work.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    balanced = n == 2 * rank
    moments = parent_moments(
        parents / f"n{n-1}_r{rank}.txt", "all", balanced,
        jobs, seconds, worker,
    )
    if not balanced:
        moments.update(parent_moments(
            parents / f"n{n-1}_r{rank-1}.txt", "coloop", False,
            jobs, seconds, worker,
        ))
    if set(moments) != {key(t) for t in partitions(n - 1)}:
        raise RuntimeError("missing parent symmetry type")
    formulas = work / "cnf"
    formulas.mkdir(exist_ok=True)
    fixed = {}
    for parts in partitions(n):
        if 1 in parts:
            smaller = list(parts)
            smaller.remove(1)
            smaller = tuple(smaller)
            numerator = centralizer(smaller) * moments[key(smaller)]
            value, remainder = divmod(numerator, math.factorial(n - 1))
            if remainder:
                raise RuntimeError(f"nonintegral fixed count for {parts}")
        else:
            value = fixed_without_point(
                n, rank, parts, formulas, jobs, seconds, solver,
            )
        fixed[key(parts)] = value
    numerator = sum(
        math.factorial(n) // centralizer(parts) * fixed[key(parts)]
        for parts in partitions(n)
    )
    unlabeled, remainder = divmod(numerator, math.factorial(n))
    if remainder:
        raise RuntimeError("nonintegral Burnside sum")
    result = {
        "n": n, "rank": rank, "unlabeled": str(unlabeled),
        "labeled": str(fixed[key((1,) * n)]),
        "fixed_terms": {t: str(v) for t, v in fixed.items()},
        "seconds": time.perf_counter() - started,
    }
    (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def elementary(n):
    partitions_of = [0] * (n + 1)
    partitions_of[0] = 1
    for part in range(1, n + 1):
        for size in range(part, n + 1):
            partitions_of[size] += partitions_of[size - part]
    rank_two = sum(partitions_of[size] - 1 for size in range(2, n + 1))
    stirling = [1] + [0] * (n + 1)
    for _ in range(1, n + 2):
        stirling = [0] + [
            stirling[k - 1] + k * stirling[k] for k in range(1, n + 2)
        ]
    return {
        0: (1, 1), 1: (n, 2**n - 1),
        2: (rank_two, sum(stirling) - 2**n),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parents", required=True, type=Path)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--rank", type=int)
    parser.add_argument("--jobs", type=int, default=64)
    parser.add_argument("--seconds", type=float, default=180)
    parser.add_argument("--worker", type=Path, default=ROOT / "build/count_extensions")
    parser.add_argument("--solver", type=Path, default=ROOT / "deps/ganak")
    args = parser.parse_args()
    if args.n < 4 or args.n > 10 or args.jobs < 1 or args.seconds <= 0:
        parser.error("unsupported n or worker settings")
    if args.rank is None and args.n != 10:
        parser.error("--rank is required unless n=10")
    ranks = [args.rank] if args.rank is not None else [3, 4, 5]
    if any(r < 2 or r > args.n // 2 for r in ranks):
        parser.error("rank must be between 2 and floor(n/2)")
    args.workdir.mkdir(parents=True, exist_ok=True)
    reports = {
        r: count_rank(
            args.n, r, args.parents, args.workdir / f"rank{r}",
            args.jobs, args.seconds, args.worker.resolve(), args.solver.resolve(),
        )
        for r in ranks
    }
    if args.rank is not None:
        row = reports[args.rank]
        result = {k: row[k] for k in ("n", "rank", "unlabeled", "labeled")}
    else:
        table = {r: {"unlabeled": str(u), "labeled": str(l)}
                 for r, (u, l) in elementary(args.n).items()}
        for r, row in reports.items():
            table[r] = {k: row[k] for k in ("unlabeled", "labeled")}
        for r in range(args.n // 2):
            table[args.n - r] = dict(table[r])
        result = {
            "n": args.n,
            "unlabeled": str(sum(int(row["unlabeled"]) for row in table.values())),
            "labeled": str(sum(int(row["labeled"]) for row in table.values())),
            "by_rank": {str(r): table[r] for r in sorted(table)},
        }
    (args.workdir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
