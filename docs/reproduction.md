# Reproduce, monitor and verify

Run commands from the repository root. The implementation supports Linux
x86-64, Python 3.10 or newer, GCC with OpenMP, Make and Boost.Multiprecision
headers. No Python packages are required.

## Build

On Ubuntu:

```bash
sudo apt-get install g++ make libboost-dev python3
python3 scripts/setup.py --audit
make -j4
make audit
make test
```

The setup script downloads Ganak v2.6.4 and, with `--audit`, nauty 2.9.3. Both
downloads are pinned by checksums. The parent generator is included as source
under `vendor/`.

`make test` takes seconds on the reference machine. It generates small parents,
audits rank functions and isomorphism classes, reproduces three full matroid
counts, checks the sparse/non-sparse split, exercises resumption and confirms
that invalid inputs are rejected. GitHub Actions runs the same suite.

The default compiler flags include `-march=native`. Build on the machine where
you will run the program. For portable binaries, override the flags:

```bash
make CXXFLAGS='-O3 -std=c++17'
```

Use a fresh checkout or remove the relevant build outputs when changing flags;
Make does not track compiler options as dependencies.

## Full count

```bash
python3 scripts/count.py --workdir runs/n10 --jobs 8 --seconds 180
```

Set `--jobs` to at most the number of available physical cores. The default is
the smaller of eight and that number. On the 64-core reference machine we used
`--jobs 64`. Each exact model-counting process has a configured cache limit of
1 GiB, so account for memory as well as CPUs when selecting the worker count.
Generated catalogues, CNF files and checkpoints require several GiB of disk.

The script generates all parents through nine elements and computes the
ten-element totals. Ranks six through ten follow by duality. The completed
result is written to `total.json`.

The repository verification run took 389.16 seconds on 64 physical cores across
two AMD EPYC 9354 CPUs, within its 6–9 minute forecast. This measures the full
calculation after compilation. Hardware, timings and checksums are recorded in
[`results/provenance.json`](../results/provenance.json).

## Monitor and resume

```bash
python3 scripts/status.py runs/n10
```

The status command is read-only. It shows parent completion counts, completed
SAT jobs and finished rank totals. Useful files are:

| Path under the work directory | Contents |
|---|---|
| `parents/generation.json` | Generator identity, output sizes and checksums |
| `sparse10/progress.json` | Sparse-paving subproblem progress |
| `rank*/parents/progress.json` | General parent progress, updated at job boundaries |
| `rank*/parents/parents.jsonl` | Completed parent moments and attempted jobs |
| `rank*/sat/` | Direct symmetry results and exact solver logs |
| `rank*/cubes_*/results/` | Results and logs for the partitioned symmetry cases |
| `rank*/result.json` | Full Burnside terms and totals for that rank |
| `total.json` | Final totals for every rank and all ranks combined |

Run the same command with the same work directory to resume. Completed parent
and SAT jobs are reused after provenance checks. Increase `--seconds` if an
individual job times out. The C++ limits are checked periodically, so they are
not strict wall-clock interruption bounds. Parent checkpoints have exclusive
writer locks; do not launch two orchestrators in the same work directory.

Use a new work directory after changing an input or rebuilding a counting
binary. Checkpoint manifests intentionally reject changed producers or inputs.
The final reduction requires every subproblem to complete.

## Generated files

The selected work directory holds parent catalogues, checkpoint ledgers, formula
files and solver logs. The `runs/`, `build/` and `deps/` directories are ignored
by Git. Compact completed-run summaries are kept in [`results/`](../results/).

## Independently audit the generated input

```bash
python3 scripts/audit.py runs/n10/parents/all_ranklines.txt \
  --out runs/n10/audit --jobs 8
```

The audit checks every rank array, duality, isomorphic duplicates and
canonical-label invariance under relabeling. It uses nauty, independently of the
counting worker's automorphism implementation. Its output includes exact
canonical rank arrays in `canonical.tsv` for later comparisons.

## Check published totals

```bash
python3 scripts/validate.py --parents runs/n10/parents \
  --ten-run runs/n10 --out runs/n10/validation --jobs 8
```

This checks all 55 known size/rank cells through nine elements, runs six
separate aggregate-counting benchmarks through nine elements, and compares the
computed ten-element ranks zero through four with published values.

## Optional comparison with Zenodo

This download is needed only for an external reference comparison:

```bash
python3 scripts/setup.py --catalogue
./build/rank_audit data/matroids09_rankLine runs/reference.tsv 8
python3 scripts/compare_catalogues.py \
  --generated runs/n10/audit/canonical.tsv --reference runs/reference.tsv \
  --out runs/n10/catalogue_comparison.json
```

The comparison checks equality of the complete sets of canonical rank strings.

## Smaller or individual stages

Generate a parent catalogue independently:

```bash
python3 scripts/generate_parents.py --through 9 --jobs 8 --out runs/parents
```

Run only the nine-element sparse-paving count:

```bash
python3 scripts/count_sparse.py 9 4 --jobs 8 --workdir runs/sparse9
```

The C++ worker's persistent stdin protocol is used by `run_parents.py`: one rank
array in, one JSON result out. The lower-level scripts expose `--help`; normal
reproduction should use `count.py` so that symmetry and coloop terms are included.
