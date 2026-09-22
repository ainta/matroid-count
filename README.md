# Counting all matroids on ten elements

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22881837.svg)](https://doi.org/10.5281/zenodo.22881837)

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

GPT-6 Astra helped discover and implement the optimized counting algorithms.
Sunghyeon Jo read the source code and mathematical proofs and verified the
correctness of the algorithms and their implementation.

## Fixed release

The [v1.0.0 release](https://github.com/ainta/matroid-count/releases/tag/v1.0.0)
provides a fixed source archive, the
[algorithm note PDF](https://github.com/ainta/matroid-count/releases/download/v1.0.0/matroid-count-n10-note.pdf),
and SHA-256 checksums. Use this version for citation and reproduction.
The source, note, and recorded results are also archived on
[Zenodo (DOI: 10.5281/zenodo.22881837)](https://doi.org/10.5281/zenodo.22881837).

Suggested citation: Jo, Sunghyeon (2026). *Counting all matroids on ten elements*
(version 1.0.0). Zenodo. https://doi.org/10.5281/zenodo.22881837

## Start here

- [Algorithm note (PDF)](docs/note.pdf) · [TeX source](docs/note.tex):
  pseudocode, correctness proofs and computation results.
- [Simple counting route](simple/README.md): one extension worker and one
  driver, using the shared parent generator and exact model counter.
- [The algorithm](docs/approach.md): the sparse-paving split, modular cuts,
  symmetry correction and why the count includes all matroids.
- [Reproduction and monitoring](docs/reproduction.md): dependencies, commands,
  checkpoints, optional catalogue comparison and resource use.
- [Verify the result](docs/validation.md): published comparisons, rank totals,
  all 42 rank-five Burnside terms and commands to reproduce them.
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

Software is licensed under [GPL-3.0-only](LICENSE). Original documentation,
the algorithm note, and recorded results are licensed under
[CC-BY-4.0](LICENSE-DOCS.md). Third-party material retains its existing licenses.

To check the arithmetic of the recorded results with Python alone:

```bash
python3 scripts/verify_results.py
```

This checks all rank totals, the sparse/non-sparse partition and the Burnside
sums. The [validation guide](docs/validation.md#recompute-and-compare) also shows
how to regenerate the counts and compare a completed run.
