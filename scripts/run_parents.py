#!/usr/bin/env python3
"""Persistent pinned workers with an exact moment ledger and restart support."""

import argparse
import collections
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
from common import physical_cpus


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("parents", type=Path)
    p.add_argument("--workdir", type=Path, required=True)
    p.add_argument("--selection", type=Path)
    p.add_argument("--mode", choices=["nonsp", "all", "coloop"], default="nonsp")
    p.add_argument("--paired-coloop", action="store_true")
    p.add_argument("--jobs", type=int, default=32)
    p.add_argument("--chunk", type=int, default=8)
    p.add_argument("--seconds-per-class", type=float, default=60)
    p.add_argument("--cache-entries", type=int, default=32768)
    a = p.parse_args()
    cpus = physical_cpus()
    if (
        not (1 <= a.jobs <= len(cpus))
        or a.chunk < 1
        or a.seconds_per_class <= 0
        or a.cache_entries < 1024
    ):
        p.error("invalid worker settings")
    start = time.perf_counter()
    work = a.workdir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    lock = (work / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lines = a.parents.read_text().splitlines(keepends=True)
    selected = (
        sorted(json.loads(a.selection.read_text()))
        if a.selection
        else list(range(len(lines)))
    )
    selected_set = set(selected)
    if len(selected_set) != len(selected) or any(
        i < 0 or i >= len(lines) for i in selected
    ):
        raise RuntimeError("invalid selection")
    manifest = {
        "parents_sha256": sha(a.parents),
        "worker_sha256": sha(ROOT / "build/extension_worker"),
        "mode": a.mode,
        "paired_coloop": a.paired_coloop,
        "selection": selected,
    }
    if (work / "manifest.json").exists() and json.loads(
        (work / "manifest.json").read_text()
    ) != manifest:
        raise RuntimeError("checkpoint provenance mismatch")
    atomic(work / "manifest.json", manifest)
    done = {}
    journal = work / "parents.jsonl"
    if journal.exists():
        with journal.open("rb+") as f:
            end = 0
            while raw := f.readline():
                if not raw.endswith(b"\n"):
                    f.truncate(end)
                    break
                row = json.loads(raw)
                end = f.tell()
                if row["row"] not in selected_set:
                    raise RuntimeError("foreign checkpoint row")
                if row["status"] == "complete":
                    if (
                        row["row"] in done
                        and done[row["row"]]["moments"] != row["moments"]
                    ):
                        raise RuntimeError("conflicting checkpoint")
                    done[row["row"]] = row
    resumed = len(done)
    out = journal.open("a", buffering=1)
    (work / "result.json").unlink(missing_ok=True)
    todo = [i for i in selected if i not in done]
    batches = queue.Queue()
    for i in range(0, len(todo), a.chunk):
        batches.put(todo[i : i + a.chunk])
    guard = threading.Lock()
    stop = threading.Event()
    processes = []
    last = time.perf_counter()
    attempts = 0

    def worker(number):
        nonlocal last, attempts
        cmd = [
            "taskset",
            "-c",
            str(cpus[number]),
            str(ROOT / "build/extension_worker"),
            a.mode,
            str(a.seconds_per_class),
            str(a.cache_entries),
            str(int(a.paired_coloop)),
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        with guard:
            processes.append(proc)
        local = 0
        try:
            while not stop.is_set():
                try:
                    batch = batches.get_nowait()
                except queue.Empty:
                    break
                for index in batch:
                    if stop.is_set():
                        break
                    proc.stdin.write(lines[index])
                    proc.stdin.flush()
                    raw = proc.stdout.readline()
                    if not raw:
                        raise RuntimeError(f"worker died: {proc.stderr.read()}")
                    row = json.loads(raw)
                    if row["row"] != local:
                        raise RuntimeError("worker sequence mismatch")
                    local += 1
                    row["row"] = index
                    row["finished_unix"] = time.time()
                    with guard:
                        out.write(json.dumps(row, separators=(",", ":")) + "\n")
                        attempts += 1
                        if row["status"] == "complete":
                            done[index] = row
                        if time.perf_counter() - last >= 15:
                            progress = {
                                "status": "running",
                                "completed": len(done),
                                "selected": len(selected),
                                "attempts": attempts,
                                "wall_seconds": time.perf_counter() - start,
                                "updated_unix": time.time(),
                            }
                            atomic(work / "progress.json", progress)
                            os.fsync(out.fileno())
                            last = time.perf_counter()
                            print(json.dumps(progress), file=sys.stderr, flush=True)
            proc.stdin.close()
            error = proc.stderr.read()
            status = proc.wait()
            if status:
                raise RuntimeError(f"worker exit {status}: {error}")
        except BaseException:
            stop.set()
            raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait()

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs)
    try:
        futures = [pool.submit(worker, i) for i in range(min(a.jobs, batches.qsize()))]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    except BaseException:
        stop.set()
        with guard:
            for proc in processes:
                if proc.poll() is None:
                    proc.terminate()
        raise
    finally:
        pool.shutdown(wait=True)
        out.flush()
        os.fsync(out.fileno())
        out.close()
    moments = collections.Counter()
    for row in done.values():
        moments.update({k: int(v) for k, v in row["moments"].items()})
    status = "complete" if len(done) == len(selected) else "partial"
    report = {
        "status": status,
        "scope": "all_parents" if len(selected) == len(lines) else "selected_parents",
        "completed": len(done),
        "selected": len(selected),
        "population": len(lines),
        "resumed": resumed,
        "moments": {k: str(v) for k, v in sorted(moments.items())},
        "jobs": a.jobs,
        "cache_entries": a.cache_entries,
        "wall_seconds": time.perf_counter() - start,
        "sum_parent_seconds": sum(row["seconds"] for row in done.values()),
    }
    atomic(work / "result.json", report)
    atomic(work / "progress.json", report)
    print(json.dumps(report, indent=2))
    return 0 if status == "complete" else 3


if __name__ == "__main__":
    sys.exit(main())
