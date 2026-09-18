# Completed computation

These files are compact records of completed calculations, not inputs to the
counter:

| File | Contents |
|---|---|
| [`counts.json`](counts.json) | Labeled and unlabeled totals at every rank, plus the rank-five sparse/non-sparse split |
| [`fixed_terms.json`](fixed_terms.json) | All 42 fixed-permutation counts for each of ranks three, four and five; rank-five non-sparse terms |
| [`validation.json`](validation.json) | Published benchmarks, independent catalogue checks and agreement with the earlier full run |
| [`provenance.json`](provenance.json) | Commands, machine/compiler information, timings and source/binary checksums |

Large integer counts are decimal strings so that JSON readers do not round
them. A cycle type such as `1.1.2.2.4` denotes a partition of ten; ten `1`s give
the identity permutation and therefore the labeled count.

The full checkpoint ledgers, generated catalogues and solver logs are rebuilt
under the selected `runs/` directory. They are intentionally not committed.
Follow [the reproduction instructions](../docs/reproduction.md) to obtain them.
