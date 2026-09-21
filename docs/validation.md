# Verify the ten-element count

The result is **3,232,000,741,644 unlabeled matroids on ten elements**.
All ranks are included, with loops, parallel elements, coloops and disconnected
matroids allowed. Isomorphism is relabeling the ground set.

## Check the recorded numbers

From the repository root, with Python 3.10 or newer:

```bash
python3 scripts/verify_results.py
```

Expected output:

```text
Passed: 126 fixed counts at ranks 3–5; rank-five sparse/non-sparse partition;
        Burnside sums, identity terms, duality, and totals over all 11 ranks.
Unlabeled: 3,232,000,741,644
Labeled:   11,727,995,799,397,397,461
```

This takes less than a second and needs no compiler or external packages.
It recomputes the arithmetic from the recorded fixed counts. To regenerate
those counts, use the full calculation below.

## How the total is assembled

| Rank | Unlabeled matroids |
|---:|---:|
| 0 | 1 |
| 1 | 10 |
| 2 | 128 |
| 3 | 10,037 |
| 4 | 4,886,380,924 |
| 5 | **3,222,227,959,444** |
| 6 | 4,886,380,924 |
| 7 | 10,037 |
| 8 | 128 |
| 9 | 10 |
| 10 | 1 |
| **Total** | **3,232,000,741,644** |

Duality gives equal counts at ranks `r` and `10-r`. Distinct dual matroids
remain distinct isomorphism classes. Rank five is computed as two disjoint
families:

| Rank-five family | Unlabeled matroids |
|---|---:|
| Sparse paving | 2,630,337,889,305 |
| Non-sparse paving | 591,890,070,139 |
| **Rank five** | **3,222,227,959,444** |

The other ranks contribute 9,772,782,200. The labeled total is obtained by
summing the numbers fixed by the identity permutation at each rank.
Both sets of rank totals are in [`counts.json`](../results/counts.json).

## Agreement with published values

Generation reproduces all **55 pairs of size and rank** through nine elements in
[Mayhew–Royle, Table 1](https://arxiv.org/pdf/math/0702316). Their sums are:

| Elements | Published and generated total |
|---:|---:|
| 0 | 1 |
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 17 |
| 5 | 38 |
| 6 | 98 |
| 7 | 306 |
| 8 | 1,724 |
| 9 | 383,172 |

The extension counter was also run separately from the generator:

| Elements | Rank | Published count | Computed count |
|---:|---:|---:|---:|
| 6 | 3 | 38 | 38 |
| 7 | 3 | 108 | 108 |
| 8 | 3 | 325 | 325 |
| 8 | 4 | 940 | 940 |
| 9 | 3 | 1,275 | 1,275 |
| 9 | 4 | 190,214 | 190,214 |
| 10 | 3 | 10,037 | 10,037 |
| 10 | 4 | 4,886,380,924 | 4,886,380,924 |

The ten-element benchmarks are listed in
[Joswig–Schröter, Table 1](https://doi.org/10.1016/j.jcta.2017.05.001).
The rank-four enumeration is due to
[Matsumoto–Moriyama–Imai–Bremner](https://doi.org/10.1007/s00454-011-9388-y).
The elementary formulas at ranks zero through two are checked as well.
Rank five is the new computed value in this repository.

## The 42 Burnside terms at rank five

For a cycle type `lambda`, let `F(lambda)` be the number of labeled matroids
fixed by one permutation of that type. If the type has `a_j` cycles of length
`j`, put `z(lambda) = product_j j^a_j a_j!`. There are `10! / z(lambda)`
permutations of that type, and

```math
u_{10,5}=\frac{1}{10!}\sum_{\lambda\vdash10}
\frac{10!}{z(\lambda)}F(\lambda).
```

Thirty types have a fixed element and use the sums over parents. The other
twelve use the basis-exchange formulas. The identity row gives the labeled
counts. Every row satisfies `All = Sparse paving + Non-sparse paving`.

<details>
<summary>Show all 42 types and their exact fixed counts</summary>

<!-- BEGIN GENERATED BURNSIDE TABLE -->
| Cycle type | Permutations of this type | All | Sparse paving | Non-sparse paving |
|---|---:|---:|---:|---:|
| 1<sup>10</sup> | 1 | 11,692,562,643,915,909,321 | 9,544,867,699,823,218,639 | 2,147,694,944,092,690,682 |
| 1<sup>8</sup> 2 | 45 | 331,520,136,243 | 53,627,906,929 | 277,892,229,314 |
| 1<sup>7</sup> 3 | 240 | 34,410,999 | 53,824 | 34,357,175 |
| 1<sup>6</sup> 2<sup>2</sup> | 630 | 164,623,547,053 | 49,888,733,139 | 114,734,813,914 |
| 1<sup>6</sup> 4 | 1,260 | 1,477,685 | 13,279 | 1,464,406 |
| 1<sup>5</sup> 2 3 | 5,040 | 1,048,209 | 2,704 | 1,045,505 |
| 1<sup>4</sup> 2<sup>3</sup> | 3,150 | 26,741,344,215 | 11,197,208,461 | 15,544,135,754 |
| 1<sup>5</sup> 5 | 6,048 | 7,806 | 4 | 7,802 |
| 1<sup>4</sup> 2 4 | 18,900 | 2,289,119 | 268,525 | 2,020,594 |
| 1<sup>4</sup> 3<sup>2</sup> | 8,400 | 36,142,788 | 12,731,470 | 23,411,318 |
| 1<sup>3</sup> 2<sup>2</sup> 3 | 25,200 | 213,991 | 576 | 213,415 |
| 1<sup>2</sup> 2<sup>4</sup> | 4,725 | 11,473,161,729 | 6,972,095,447 | 4,501,066,282 |
| 1<sup>4</sup> 6 | 25,200 | 9,324 | 250 | 9,074 |
| 1<sup>3</sup> 2 5 | 60,480 | 1,788 | 4 | 1,784 |
| 1<sup>3</sup> 3 4 | 50,400 | 7,793 | 64 | 7,729 |
| 1<sup>2</sup> 2<sup>2</sup> 4 | 56,700 | 1,104,289 | 171,099 | 933,190 |
| 1<sup>2</sup> 2 3<sup>2</sup> | 50,400 | 133,782 | 7,744 | 126,038 |
| 1 2<sup>3</sup> 3 | 25,200 | 63,585 | 400 | 63,185 |
| 2<sup>5</sup> | 945 | 584,746,603 | 217,942,377 | 366,804,226 |
| 1<sup>3</sup> 7 | 86,400 | 517 | 79 | 438 |
| 1<sup>2</sup> 2 6 | 151,200 | 12,138 | 2,828 | 9,310 |
| 1<sup>2</sup> 3 5 | 120,960 | 339 | 4 | 335 |
| 1<sup>2</sup> 4<sup>2</sup> | 56,700 | 697,677 | 398,135 | 299,542 |
| 1 2<sup>2</sup> 5 | 90,720 | 618 | 4 | 614 |
| 1 2 3 4 | 151,200 | 3,143 | 16 | 3,127 |
| 1 3<sup>3</sup> | 22,400 | 1,529,040 | 799,876 | 729,164 |
| 2<sup>3</sup> 4 | 18,900 | 792,347 | 34,257 | 758,090 |
| 2<sup>2</sup> 3<sup>2</sup> | 25,200 | 104,620 | 16,542 | 88,078 |
| 1<sup>2</sup> 8 | 226,800 | 723 | 375 | 348 |
| 1 2 7 | 259,200 | 135 | 9 | 126 |
| 1 3 6 | 201,600 | 4,524 | 1,276 | 3,248 |
| 1 4 5 | 181,440 | 110 | 4 | 106 |
| 2<sup>2</sup> 6 | 75,600 | 5,620 | 1,146 | 4,474 |
| 2 3 5 | 120,960 | 129 | 4 | 125 |
| 2 4<sup>2</sup> | 56,700 | 150,791 | 53,705 | 97,086 |
| 3<sup>2</sup> 4 | 50,400 | 1,022 | 16 | 1,006 |
| 1 9 | 403,200 | 111 | 70 | 41 |
| 2 8 | 226,800 | 637 | 389 | 248 |
| 3 7 | 172,800 | 28 | 1 | 27 |
| 4 6 | 151,200 | 746 | 132 | 614 |
| 5<sup>2</sup> | 72,576 | 24,566 | 21,969 | 2,597 |
| 10 | 362,880 | 78 | 67 | 11 |
<!-- END GENERATED BURNSIDE TABLE -->

</details>

The table is generated from [`fixed_terms.json`](../results/fixed_terms.json),
which also includes all 42 terms at ranks three and four. In that file, cycle
lengths are separated by dots: `1.1.2.2.4` means two fixed elements, two
transpositions and one cycle of length four. Counts are decimal strings to
preserve all digits in software that uses floating-point JSON numbers.

## Checks of the parent catalogue

The generator starts from the empty matroid and produces all 385,370 classes
through nine elements. A separate audit uses nauty to canonically label the
element/hyperplane incidence graphs. It checks the rank axioms, duality,
isomorphic duplicates and invariance under relabeling.

Comparison with the [Mayhew–Royle catalogue](https://zenodo.org/records/6825419)
found exact equality of the complete sets of canonical rank arrays: zero
missing classes, extra classes or isomorphic duplicates. The audit checks
196,672,421 rank bounds, 884,753,266 rank increments and 1,768,978,636 local
submodularity inequalities per catalogue, and checks the duals too.

Nauty independently reproduced all 190,214 parent automorphism orders used at
rank five. Regenerating the parents and relabeling them preserved every vector
of weighted sums over automorphisms. The complete rerun reproduced all 126
fixed counts at ranks three through five, plus all 42 non-sparse-paving terms.
These full reruns use the same extension-counting implementation.

## Recompute and compare

First follow the [build instructions](reproduction.md#build). Then run:

```bash
# Regenerate the inputs and every counting stage.
python3 scripts/count.py --workdir runs/n10 --jobs 8 --seconds 180

# Compare all rank totals and fixed counts with the recorded results.
python3 scripts/verify_results.py --run runs/n10

# Reproduce the published benchmarks, including the six aggregate checks.
python3 scripts/validate.py --parents runs/n10/parents \
  --ten-run runs/n10 --out runs/n10/validation --jobs 8

# Independently audit ranks, isomorphism classes and duality.
python3 scripts/audit.py runs/n10/parents/all_ranklines.txt \
  --out runs/n10/audit --jobs 8
```

The recorded full calculation took **6 minutes 29 seconds on 64 physical CPU
cores**, after compilation. See the [reproduction guide](reproduction.md) for
memory, disk, monitoring, resumption and the optional external-catalogue
comparison. Published totals are test expectations; they are not inputs to
the counting algorithm.

## Evidence files

| File | Contents |
|---|---|
| [`results/counts.json`](../results/counts.json) | Labeled and unlabeled counts at every rank; rank-five partition |
| [`results/fixed_terms.json`](../results/fixed_terms.json) | All fixed counts at ranks 3–5 and the rank-five non-sparse-paving counts |
| [`results/validation.json`](../results/validation.json) | Published comparisons, catalogue audit and completed rerun comparisons |
| [`results/provenance.json`](../results/provenance.json) | Recorded commands, hardware, compiler, timings and source/binary checksums |
| [`docs/note.pdf`](note.pdf) | Algorithms, correctness proofs and calculation results |

Full parent ledgers, formulas and solver logs are generated in the chosen run
directory. They are kept out of Git and can be distributed as a separate
release attachment. The [reproduction guide](reproduction.md#monitor-and-resume)
lists their locations. The final reduction checks that every subproblem is
complete; timed-out jobs do not supply counts.

To refresh the displayed table after changing the recorded results:

```bash
python3 scripts/verify_results.py --write-table docs/validation.md
```

`make verify` checks the arithmetic, table consistency and rejection of
incomplete or inconsistent result files. It uses only Python and is also run
in CI.
