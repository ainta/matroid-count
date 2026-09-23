# Counting all matroids on ten elements

The number of matroids on ten elements up to isomorphism is
**3,232,000,741,644**. The number with labeled elements is
11,727,995,799,397,397,461.

The [blog post](https://ainta.github.io/2026-09-22-counting-all-matroids-on-ten-elements/)
explains the algorithm. This repository contains the code, recorded counts,
and tests needed to reproduce the calculation. It generates the nine-element
matroids, counts their extensions as modular cuts, and uses Burnside's lemma
to obtain the ten-element counts. Permutations without a fixed point use
exact model counting of invariant basis families.

## Reproduce

On Linux x86-64, install Python 3.10 or newer, GCC with C++17 support, Make,
and Boost headers. From the repository root, run:

```sh
python3 scripts/setup.py
make -j4
python3 scripts/generate_parents.py --through 9 --jobs 64 --out runs/n10/parents
python3 -S scripts/count.py --parents runs/n10/parents --workdir runs/n10/count --jobs 64
python3 scripts/verify_results.py --run runs/n10/count
```

Set `--jobs` to the number of available physical cores. The result is in
`runs/n10/count/result.json`. The recorded result and all 42 fixed counts
for each of ranks 3–5 are in [`results/`](results/). The run took about
ten minutes with 64 workers on two AMD EPYC 9354 CPUs. Ganak, downloaded
by `setup.py`, can use up to 1 GiB of cache per process.

## Check smaller cases

```sh
python3 scripts/setup.py --audit
make -j4 audit test verify
```

The tests reproduce the published counts 38 at $(n,r)=(6,3)$, 108 at
$(7,3)$, 940 at $(8,4)$, and 190,214 at $(9,4)$. They also audit the
generated parents with nauty. `make verify` checks the recorded fixed
counts, Burnside sums, duality, and totals. The optional full comparison
with the [public nine-element catalogue](https://zenodo.org/records/6825419)
is recorded in [`results/catalogue-comparison.json`](results/catalogue-comparison.json).
The public catalogue is not an input to the count.

The pinned parent generator is in [`vendor/matroid-generator/`](vendor/matroid-generator/).
Third-party sources and licenses are listed in [`THIRD_PARTY.md`](THIRD_PARTY.md).
Software is licensed under [GPL-3.0-only](LICENSE); original documentation
and recorded results are licensed under [CC-BY-4.0](LICENSE-DOCS.md).

GPT-6 Astra helped discover and implement the optimized algorithms.
Sunghyeon Jo read the source code and mathematical proofs and verified
the correctness of the algorithms and their implementation.
