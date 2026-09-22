# Validation

The repository records the total in [result.json](../results/result.json)
and all 42 fixed-permutation counts for each computed rank in the
[rank-three](../results/rank3/result.json),
[rank-four](../results/rank4/result.json), and
[rank-five](../results/rank5/result.json) reports.

## Known counts

The parent generator starts from the empty matroid. Its nine-element
output has 383,172 isomorphism classes, as reported by
[Mayhew and Royle](https://arxiv.org/pdf/math/0702316).
The optional [nauty audit](reproduction.md#audit-the-generated-parents)
checks all generated rank arrays, isomorphic duplicates, and duals.
A separate comparison checks the complete canonical catalogue against
the published [nine-element data](https://zenodo.org/records/6825419).
The [generation record](../results/generation.json),
[audit](../results/audit.json), and
[catalogue comparison](../results/catalogue-comparison.json) are included
with the count.

The counting worker reproduces these published rank counts:

| Ground-set size | Rank | Isomorphism classes |
|---:|---:|---:|
| 6 | 3 | 38 |
| 7 | 3 | 108 |
| 8 | 4 | 940 |
| 9 | 4 | 190,214 |
| 10 | 3 | 10,037 |
| 10 | 4 | 4,886,380,924 |

The values through nine elements appear in
[Mayhew and Royle, Table 1](https://arxiv.org/pdf/math/0702316).
The ten-element rank-three count appears in
[Joswig and Schröter, Table 1](https://doi.org/10.1016/j.jcta.2017.05.001).
The ten-element rank-four count is from
[Matsumoto, Moriyama, Imai, and Bremner](https://doi.org/10.1007/s00454-011-9388-y).

## Ten-element result

| Rank | Unlabeled | Labeled |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 10 | 1,023 |
| 2 | 128 | 677,546 |
| 3 | 10,037 | 16,869,404,175 |
| 4 | 4,886,380,924 | 17,716,560,870,661,325 |
| 5 | 3,222,227,959,444 | 11,692,562,643,915,909,321 |

Duality gives ranks six through ten from ranks four through zero.
The resulting totals are 3,232,000,741,644 unlabeled and
11,727,995,799,397,397,461 labeled matroids.

For each rank from three to five, the result checker verifies that the
identity fixed count equals the labeled count. It recomputes Burnside's
sum from all 42 cycle types and checks that the sum equals the reported
unlabeled count. It also checks duality and the totals over all ranks.
Run make verify to check the recorded data. After a new count, run
scripts/verify_results.py with --run to compare every fixed count with
the recorded data.
