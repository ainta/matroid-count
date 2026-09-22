# Counting all matroids on ten elements

This repository counts matroids on ten elements up to isomorphism.
It counts extensions of nine-element matroids without constructing
the ten-element matroids one by one.

| Quantity | Count |
|---|---:|
| Isomorphism classes | **3,232,000,741,644** |
| Labeled matroids | 11,727,995,799,397,397,461 |

The code uses one extension counter for every parent. It counts modular
cuts, reduces the remaining hyperplane choices to independent sets,
and uses Burnside's lemma to count isomorphism classes. For permutations
without a fixed point, it counts invariant basis families with Ganak.
The [method](docs/approach.md) gives the formulas and correctness argument.

GPT-6 Astra helped discover and implement the optimized counting algorithms.
Sunghyeon Jo read the source code and mathematical proofs and verified the
correctness of the algorithms and their implementation.

## Reproduce

The commands below require Linux x86-64, Python 3.10 or newer, GCC,
Make, and Boost headers. Run them from the repository root.

~~~bash
python3 scripts/setup.py
make -j4
python3 scripts/generate_parents.py --through 9 --jobs 64 \
    --out runs/n10/parents
python3 -S scripts/count.py --parents runs/n10/parents \
    --workdir runs/n10/count --jobs 64
python3 scripts/verify_results.py --run runs/n10/count
~~~

Use the number of available physical cores for --jobs. The full
count took about ten minutes with 64 workers on two AMD EPYC 9354 CPUs.
The result is written to runs/n10/count/result.json. See the
[reproduction guide](docs/reproduction.md) for tests, an independent
audit of the parents, and resource details.

## Files

| Path | Purpose |
|---|---|
| [scripts/count.py](scripts/count.py) | Run the extension workers, count fixed basis families, and apply Burnside's lemma |
| [src/count_extensions.cpp](src/count_extensions.cpp) | Count invariant modular cuts with constraint propagation and independent sets |
| [scripts/generate_parents.py](scripts/generate_parents.py) | Generate the nine-element parent catalogue from the empty matroid |
| [vendor/matroid-generator/](vendor/matroid-generator/) | Pinned source for the parent generator |
| [results/](results/) | Recorded totals and all fixed-permutation counts |
| [docs/validation.md](docs/validation.md) | Published comparisons and checks |

For the smaller tests, run python3 scripts/setup.py --audit and then make test.
The tests reproduce four published counts. Run make verify to check the
recorded ten-element results. The [third-party attribution](THIRD_PARTY.md)
identifies the upstream generator, Ganak, nauty, and optional reference data.

The [v1.0.0 release](https://github.com/ainta/matroid-count/releases/tag/v1.0.0)
and [Zenodo archive](https://doi.org/10.5281/zenodo.22881837) preserve
the earlier source and algorithm note. The current branch contains the
single counting route described above.

Software is licensed under [GPL-3.0-only](LICENSE). Original documentation
and recorded results are licensed under [CC-BY-4.0](LICENSE-DOCS.md).
