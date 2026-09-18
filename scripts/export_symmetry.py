#!/usr/bin/env python3
"""Basis-exchange CNF with one variable per subset orbit, no auxiliaries."""

import argparse
import itertools
import json
from pathlib import Path


def partitions(n, least=1):
    if n == 0:
        yield ()
    for k in range(least, n + 1):
        for tail in partitions(n - k, k):
            yield (k,) + tail


def export(n, r, cycle_type, path):
    blocks = [sum(1 << i for i in c) for c in itertools.combinations(range(n), r)]
    index = {b: i for i, b in enumerate(blocks)}
    perm = list(range(n))
    off = 0
    for size in cycle_type:
        for i in range(size):
            perm[off + i] = off + (i + 1) % size
        off += size
    image = lambda b: sum(1 << perm[i] for i in range(n) if b >> i & 1)
    orbit = [-1] * len(blocks)
    nv = 0
    for i, b in enumerate(blocks):
        if orbit[i] >= 0:
            continue
        nv += 1
        t = b
        while orbit[index[t]] < 0:
            orbit[index[t]] = nv
            t = image(t)
    clauses = {tuple(range(1, nv + 1))}
    for i, b in enumerate(blocks):
        for j, c in enumerate(blocks):
            left, right = b & ~c, c & ~b
            while left:
                e = left & -left
                left -= e
                clause = {-orbit[i], -orbit[j]}
                scan = right
                while scan:
                    f = scan & -scan
                    scan -= f
                    clause.add(orbit[index[(b ^ e) | f]])
                if not any(-v in clause for v in clause):
                    clauses.add(tuple(sorted(clause)))
    with path.open("w") as out:
        out.write(f"c t mc\np cnf {nv} {len(clauses)}\n")
        for clause in sorted(clauses):
            out.write(" ".join(map(str, clause)) + " 0\n")
    return {
        "n": n,
        "r": r,
        "cycle_type": cycle_type,
        "variables": nv,
        "clauses": len(clauses),
        "file": str(path),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("n", type=int)
    p.add_argument("r", type=int)
    p.add_argument("out", type=Path)
    p.add_argument("--all-types", action="store_true")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = [
        export(a.n, a.r, t, a.out / ("_".join(map(str, t)) + ".cnf"))
        for t in partitions(a.n)
        if a.all_types or 1 not in t
    ]
    (a.out / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))
