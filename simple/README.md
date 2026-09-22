# Simple counting route

This directory contains the shorter route to the same ten-element count.
`worker.cpp` counts one-element extensions by modular cuts and independent
sets; `count.py` combines those counts with exact symmetry counts and
Burnside's lemma. Every parent uses the same extension counter. The route does
not split off sparse paving matroids.

The nine-element parent generator and the checksum-pinned Ganak model counter
are shared with the main repository. From the repository root:

```bash
python3 scripts/setup.py
make -j4 build/compact_worker build/colex_to_rank vendor/matroid-generator/build/IC
python3 -S scripts/generate_parents.py --through 9 --jobs 64 \
    --out runs/simple/parents
python3 -S simple/count.py --parents runs/simple/parents \
    --workdir runs/simple/count --jobs 64
```

The answer is written to `runs/simple/count/result.json`:
3,232,000,741,644 unlabeled and 11,727,995,799,397,397,461 labeled
matroids, across all ranks. Each `rank*/result.json` also contains its 42
fixed-permutation counts. The completed run from generated parents took about
ten minutes with 64 workers on two AMD EPYC 9354 processors.

To check smaller published values with the same code, use `--n` and `--rank`:

```bash
python3 -S simple/count.py --n 9 --rank 4 \
    --parents runs/simple/parents --workdir runs/simple/check9 --jobs 64
```

This gives 190,214. `make test` also checks ranks three and four at six, seven,
and eight elements against the main pipeline; `make verify` checks the recorded
ten-element results.
