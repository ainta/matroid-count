# Counting all matroids on ten elements

An exact, parallel counting pipeline for **all matroids on ten elements**, at
every rank, including loops, parallel elements, coloops and disconnected
matroids. Isomorphism means relabeling the ground set; distinct dual matroids
remain distinct classes.

| Computed quantity | Count |
|---|---:|
| Unlabeled, all ranks | **3,232,000,741,644** |
| Labeled, all ranks | **11,727,995,799,397,397,461** |

The pipeline generates its own smaller parents from the empty matroid. Published
counts and the external catalogue are used for verification, never to fill in a
summand. It counts extensions in aggregate rather than writing trillions of
individual ten-element representatives.

## Start here

- [The algorithm](docs/approach.md): the sparse-paving split, modular cuts,
  symmetry correction and why the count includes all matroids.
- [Reproduction and monitoring](docs/reproduction.md): dependencies, commands,
  checkpoints, optional catalogue comparison and resource use.
- [Validation](docs/validation.md): published benchmarks, independent input
  checks, and what has not been independently replicated.
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

`setup.py` downloads checksum-pinned tools, not a matroid catalogue. Use
`--jobs 64` on a machine with 64 available physical cores. The original full run
took **6 minutes 26 seconds** on two AMD EPYC 9354 CPUs using 64 cores; the
forecast recorded beforehand was 5–9 minutes. This excludes compilation and
development. Runtime depends on the machine and worker count.

The answer is written to `runs/n10/total.json`. While it runs:

```bash
python3 scripts/status.py runs/n10
```

Afterward, independently audit its generated parents and compare known counts:

```bash
python3 scripts/audit.py runs/n10/parents/all_ranklines.txt \
  --out runs/n10/audit --jobs 8
python3 scripts/validate.py --parents runs/n10/parents \
  --ten-run runs/n10 --out runs/n10/validation --jobs 8
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

Build outputs, downloaded tools and generated run data are ignored by Git. See
[third-party attribution](THIRD_PARTY.md) for the upstream code and tools used.

The ten-element result is a computation from this implementation. Known counts
and the input catalogue were checked extensively; the full rank-five count has
not yet been replicated with a second independent counting implementation.
