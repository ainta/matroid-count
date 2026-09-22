# Recorded count

The count files use the same layout as a completed scripts/count.py run.
The other files record checks of the parent input.

| File | Contents |
|---|---|
| [result.json](result.json) | Labeled and unlabeled totals at every rank |
| [rank3/result.json](rank3/result.json) | Rank-three total and 42 fixed-permutation counts |
| [rank4/result.json](rank4/result.json) | Rank-four total and 42 fixed-permutation counts |
| [rank5/result.json](rank5/result.json) | Rank-five total and 42 fixed-permutation counts |
| [generation.json](generation.json) | Generator identity and hashes of the parent files |
| [audit.json](audit.json) | Independent checks of rank axioms, uniqueness, and duality |
| [catalogue-comparison.json](catalogue-comparison.json) | Full canonical comparison with the public catalogue |

Counts are decimal strings. A key such as 1.1.2.2.4 gives the lengths of
the permutation cycles. Ten 1s describe the identity permutation, so
that entry is the labeled count.

Run make verify to recompute the Burnside sums and check ranks and totals.
To compare a new run with every recorded fixed count, run
scripts/verify_results.py with --run. The [reproduction guide](../docs/reproduction.md)
gives the complete commands.
