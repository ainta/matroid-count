#!/usr/bin/env python3
"""Parallel, resumable sparse-paving count using the original C++ kernels.

Persistent split_count processes read /dev/stdin and keep private caches.
The order-five inclusion-exclusion table is built once, in a separate process.
Each completed row is saved before it contributes to the final exact sum.
"""

import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent / "build"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


from common import physical_cpus


def checked_json(command):
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    if data["status"] != "complete":
        raise RuntimeError(f"Incomplete computation: {data}")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", type=int)
    parser.add_argument("r", type=int)
    parser.add_argument("--jobs", type=int, default=min(32, len(physical_cpus())))
    parser.add_argument("--chunk-size", type=int, default=32)
    parser.add_argument("--cache-entries", type=int, default=32_768)
    parser.add_argument("--seconds-per-root", type=float, default=300)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument(
        "--selection",
        type=Path,
        help="JSON list of parent row IDs (or objects with parent_row); pilot only",
    )
    args = parser.parse_args()
    cpus = physical_cpus()
    if not (3 <= args.n <= 10 and 2 <= args.r < args.n):
        parser.error("require 3 <= n <= 10 and 2 <= r < n")
    if not (1 <= args.jobs <= len(cpus)):
        parser.error(f"jobs must be between 1 and {len(cpus)} available physical cores")
    if args.chunk_size < 1 or args.cache_entries < 1024 or args.seconds_per_root <= 0:
        parser.error(
            "positive chunk size and time limit, and cache entries >= 1024 required"
        )
    work = args.workdir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    lock = (work / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.perf_counter()
    parents = work / "parents.tsv"
    generation = work / "parent_generation.json"
    if not (parents.exists() and generation.exists()):
        temp = work / "parents.tmp"
        data = checked_json(
            [
                str(ROOT / "augment_sparse"),
                str(args.n - 1),
                str(args.r - 1),
                "300",
                str(temp),
            ]
        )
        temp.replace(parents)
        atomic_json(generation, data)
    parent_data = json.loads(generation.read_text())
    if (parent_data["n"], parent_data["r"], parent_data["status"]) != (
        args.n - 1,
        args.r - 1,
        "complete",
    ):
        raise RuntimeError("Parent catalogue belongs to another computation")
    lines = parents.read_text().splitlines(keepends=True)
    fields = [list(map(int, line.split())) for line in lines]
    if len(lines) != parent_data["unlabeled"]:
        raise RuntimeError("Incomplete parent catalogue")
    factorial = math.factorial(args.n - 1)
    for k, hi, lo, aut in fields:
        if (hi << 64 | lo).bit_count() != k or aut <= 0 or factorial % aut:
            raise RuntimeError("Malformed parent catalogue")
    if sum(factorial // row[3] for row in fields) != int(parent_data["labeled"]):
        raise RuntimeError("Parent orbit-weight sum mismatch")
    selected = list(range(len(lines)))
    if args.selection:
        selection = json.loads(args.selection.read_text())
        selected = [
            row["parent_row"] if isinstance(row, dict) else row for row in selection
        ]
        if len(set(selected)) != len(selected) or any(
            i < 0 or i >= len(lines) for i in selected
        ):
            raise RuntimeError("Invalid selection")
        selected.sort()  # Keep the catalogue's depth-first locality.
    selected_set = set(selected)
    manifest = {
        "n": args.n,
        "r": args.r,
        "parents_sha256": digest(parents),
        "selection_sha256": hashlib.sha256(json.dumps(selected).encode()).hexdigest(),
        "kernels": {
            name: digest(ROOT / name)
            for name in ("augment_sparse", "split_count", "burnside_sparse")
        },
    }
    manifest_path = work / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise RuntimeError("Checkpoint provenance changed; use a new work directory")
    atomic_json(manifest_path, manifest)
    complete = {}

    def validate(record):
        row = record["row"]
        if row not in selected_set or record["k"] != fields[row][0]:
            raise RuntimeError("Root does not match parent identity")
        if record["status"] == "complete":
            if (
                record["weight"] != factorial // fields[row][3]
                or int(record["count"]) < 1
            ):
                raise RuntimeError("Invalid completed root")
            if row in complete and any(
                record[key] != complete[row][key] for key in ("count", "weight")
            ):
                raise RuntimeError("Conflicting duplicate root")

    journal = work / "roots.jsonl"
    if journal.exists():
        # Ignore only a torn final write. Never silently ignore a complete bad row.
        with journal.open("rb+") as handle:
            position = 0
            while raw := handle.readline():
                if not raw.endswith(b"\n"):
                    handle.truncate(position)
                    break
                record = json.loads(raw)
                validate(record)
                if record["status"] == "complete":
                    complete[record["row"]] = record
                position = handle.tell()
    resumed = len(complete)
    for name in ("result.json", "subset.json"):
        (work / name).unlink(missing_ok=True)
    output = journal.open("a", buffering=1)
    write_lock = threading.Lock()
    last_progress = time.perf_counter()

    def save(record, row):
        nonlocal last_progress
        record["row"] = row
        record["finished_unix"] = time.time()
        with write_lock:
            validate(record)
            output.write(json.dumps(record, separators=(",", ":")) + "\n")
            if record["status"] == "complete":
                complete[row] = record
            if time.perf_counter() - last_progress >= 15:
                print(
                    f"{len(complete)}/{len(selected)} roots complete; "
                    f"{time.perf_counter() - started:.1f}s this invocation",
                    file=sys.stderr,
                    flush=True,
                )
                os.fsync(output.fileno())
                atomic_json(
                    work / "progress.json",
                    {
                        "status": "running",
                        "completed_roots": len(complete),
                        "selected_roots": len(selected),
                        "resumed_roots": resumed,
                        "wall_seconds": time.perf_counter() - started,
                        "updated_unix": time.time(),
                    },
                )
                last_progress = time.perf_counter()

    def command(input_path):
        return [
            str(ROOT / "split_count"),
            str(args.n),
            str(args.r),
            str(input_path),
            str(args.seconds_per_root),
            "0",
            str(2**63 - 1),
            str(args.cache_entries),
        ]

    low = [
        i
        for i in selected
        if i not in complete and (args.n, args.r) == (10, 5) and fields[i][0] <= 5
    ]
    if low:
        low_file = work / "low.tsv"
        low_file.write_text("".join(lines[i] for i in low))
        result = subprocess.run(
            ["taskset", "-c", str(cpus[0]), *command(low_file), str(parents)],
            text=True,
            capture_output=True,
        )
        (work / "low_summary.json").write_text(result.stderr)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        if result.returncode or len(records) != len(low):
            raise RuntimeError(f"Low-order calculation failed: {result.stderr}")
        for local, record in enumerate(records):
            if record["row"] != local or record["status"] != "complete":
                raise RuntimeError("Incomplete low-order calculation")
            save(record, low[local])

    pending = [i for i in selected if i not in complete]
    batches = queue.Queue()
    for begin in range(0, len(pending), args.chunk_size):
        batches.put(pending[begin : begin + args.chunk_size])
    stop = threading.Event()
    processes = []
    process_lock = threading.Lock()

    def worker(number):
        process = subprocess.Popen(
            ["taskset", "-c", str(cpus[number]), *command("/dev/stdin")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        with process_lock:
            processes.append(process)
        local_row = 0
        expected_total = 0
        try:
            while not stop.is_set():
                try:
                    batch = batches.get_nowait()
                except queue.Empty:
                    break
                for row in batch:
                    if stop.is_set():
                        break
                    process.stdin.write(lines[row])
                    process.stdin.flush()
                    raw = process.stdout.readline()
                    if not raw:
                        raise RuntimeError(
                            f"Worker {number} stopped: {process.stderr.read()}"
                        )
                    record = json.loads(raw)
                    if record["row"] != local_row:
                        raise RuntimeError("Worker row sequence mismatch")
                    local_row += 1
                    if record["status"] == "complete":
                        expected_total += int(record["count"]) * record["weight"]
                    save(record, row)
            process.stdin.close()
            stderr = process.stderr.read()
            status = process.wait()
            (work / f"worker_{number:03}.json").write_text(stderr)
            if status not in (0, 3):
                raise RuntimeError(f"Worker {number} failed: {stderr}")
            summary = json.loads(stderr)
            if int(summary["total"]) != expected_total or summary["roots"] != local_row:
                raise RuntimeError("Worker summary does not match root records")
        except BaseException:
            stop.set()
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs)
    try:
        futures = [
            pool.submit(worker, i) for i in range(min(args.jobs, batches.qsize()))
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    except BaseException:
        stop.set()
        with process_lock:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
        raise
    finally:
        pool.shutdown(wait=True)
        output.flush()
        os.fsync(output.fileno())
        output.close()
    if set(complete) != selected_set:
        raise RuntimeError(
            f"Incomplete: {len(complete)}/{len(selected)} roots; rerun to retry missing roots"
        )
    total = sum(int(row["count"]) * row["weight"] for row in complete.values())
    report = {
        "status": "complete" if len(selected) == len(lines) else "subset",
        "class": "sparse paving",
        "n": args.n,
        "r": args.r,
        "parent_orbits": len(lines),
        "completed_roots": len(complete),
        "resumed_roots": resumed,
        "weighted_sum": str(total),
        "jobs": args.jobs,
        "physical_cpus": cpus[: args.jobs],
        "chunk_size": args.chunk_size,
        "cache_entries": args.cache_entries,
    }
    if report["status"] == "complete":
        burnside = checked_json(
            [
                str(ROOT / "burnside_sparse"),
                str(args.n),
                str(args.r),
                str(total),
                str(args.seconds_per_root),
            ]
        )
        report.update(
            labeled=str(total), unlabeled=burnside["unlabeled"], burnside=burnside
        )
    report["wall_seconds"] = time.perf_counter() - started
    atomic_json(
        work / ("result.json" if report["status"] == "complete" else "subset.json"),
        report,
    )
    atomic_json(work / "progress.json", {**report, "updated_unix": time.time()})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
