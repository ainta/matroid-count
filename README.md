# Counting all matroids on ten elements

An exact, parallel counting pipeline for **all matroids on ten elements**, at
every rank, including loops, parallel elements, coloops and disconnected
matroids. Isomorphism means relabeling the ground set; distinct dual matroids
remain distinct classes.

| Computed quantity | Count |
|---|---:|
| Unlabeled, all ranks | **3,232,000,741,644** |
| Labeled, all ranks | **11,727,995,799,397,397,461** |

The pipeline generates smaller parents from the empty matroid and counts their
extensions in aggregate. Published counts and a reference catalogue provide
validation checks.

## Start here

- [Algorithm note (PDF)](docs/note.pdf) · [TeX source](docs/note.tex):
  pseudocode, correctness proofs and computation results.
- [The algorithm](docs/approach.md): the sparse-paving split, modular cuts,
  symmetry correction and why the count includes all matroids.
- [Reproduction and monitoring](docs/reproduction.md): dependencies, commands,
  checkpoints, optional catalogue comparison and resource use.
- [Validation](docs/validation.md): published benchmarks and catalogue checks.
- [Machine-readable results](results/): totals, fixed-permutation counts,
  validation evidence and provenance.

## Quick start

Requires **Linux x86-64**, Python 3.10+, GCC with OpenMP, Make, and Boost headers.
On Ubuntu, install `g++ make libboost-dev python3` first. Run from this directory:

```bash
python3 scripts/setup.py --audit
make -j4
make audit
make test
python3 scripts/count.py --workdir runs/n10 --jobs 8
```

Use `--jobs 64` on a machine with 64 available physical cores. A full run took
**6 minutes 29 seconds** on two AMD EPYC 9354 CPUs. See the
[reproduction guide](docs/reproduction.md) for dependencies and resource use.

The answer is written to `runs/n10/total.json`. While it runs:

```bash
python3 scripts/status.py runs/n10
```

## Repository map

| Directory | Purpose |
|---|---|
| `src/` | Exact C++ generators, counters, rank conversion and independent audit |
| `scripts/` | Run orchestration, checkpoints, symmetry formulas and validation |
| `tests/` | Small end-to-end counts and failure/restart checks |
| `docs/` | Mathematical approach, reproduction and validation |
| `results/` | Compact evidence from completed runs |
| `vendor/matroid-generator/` | Pinned upstream parent-generator source and license |

See [third-party attribution](THIRD_PARTY.md) for the upstream code and tools used.
