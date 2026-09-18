# Evidence and limits

The final pipeline was run from the empty matroid with no downloaded catalogue
or supplied count as an input. Verification combines known-count benchmarks,
an independently generated catalogue, a separate rank/isomorphism audit, and
exact accounting of every required subproblem.

## Known values

All 55 size/rank entries from zero through nine elements match Table 1 of
[Mayhew–Royle](https://arxiv.org/pdf/math/0702316). The total at nine elements is
383,172; ranks four and five each have 190,214 classes.

The aggregate extension counter was also exercised separately from the
generator:

| Elements | Rank | Computed and expected unlabeled count |
|---:|---:|---:|
| 6 | 3 | 38 |
| 7 | 3 | 108 |
| 8 | 3 | 325 |
| 8 | 4 | 940 |
| 9 | 3 | 1,275 |
| 9 | 4 | 190,214 |
| 10 | 3 | 10,037 |
| 10 | 4 | 4,886,380,924 |

The ten-element benchmarks appear in Table 1 of
[Joswig–Schröter](https://doi.org/10.1016/j.jcta.2017.05.001), with the rank-four
enumeration attributed to Matsumoto–Moriyama–Imai–Bremner. The rank-zero,
rank-one and rank-two formulas were checked too. None of those published
values supplies a term of the production answer.

## Verify the actual catalogue, not just its size

Independent generation produced all 385,370 classes from zero through nine
elements. Comparing full canonical rank arrays against the
[Mayhew–Royle catalogue](https://zenodo.org/records/6825419) found no missing
classes, extra classes or isomorphic duplicates.

For every entry, the independent C++ audit checks:

- Zero rank for the empty set and the rank bounds for every subset.
- Every one-element rank increment and every local submodularity inequality.
- Reconstruction of ranks from independent sets, and validity of the dual.
- Canonicalization of the element/hyperplane incidence graph with the two
  vertex colors fixed, using nauty.
- Equality of canonical rank strings after a deterministic relabeling.
- Dual closure of the complete class set.

Local submodularity gives diminishing returns along every inclusion chain and
therefore full submodularity. This is an exhaustive equivalent test of the rank
axioms, not a random subset of them. For each catalogue the original rank arrays
receive 196,672,421 bound checks, 884,753,266 increment checks and
1,768,978,636 submodular-square checks; the dual arrays receive the same tests.

Nauty also independently reproduced all 190,214 automorphism orders used in the
original rank-five parent run. After replacing the catalogue with independently
generated and differently labeled parents, every per-parent moment vector
matched the earlier run exactly.

## Accounting and implementation checks

Every parent row must complete and be present exactly once in the reduced
ledger. Automorphism groups are enumerated exactly; invariant signatures only
prune candidate permutations. Every retained permutation preserves the whole
rank array. Conjugacy-class sizes must cover the group.

Every fixed-point cycle type is checked for integral conversion from its integer
moment. Every derangement instance, including all 256 assignments in each hard
case, must complete. Ganak logs must report an exact integer and
`epsilon: 0 delta: 0`. The final Burnside numerator must be divisible by $n!$.

Small tests additionally compare the non-sparse-paving moment calculation with
the difference between independently computed full and sparse-paving fixed
counts. They exercise the paired coloop term, resumption of completed parent
jobs, invalid rank-array rejection and isomorphic-duplicate rejection.

## What this does not establish

The full ten-element rank-five computation has not been repeated using a second
independent counting implementation. Regenerating its inputs, changing their
labels and checking known cases provide substantial validation, but do not
replace that independent replication or constitute a formal proof of the
software. No claim of external review of the new total is made.

Only compact result summaries are committed. Full parent ledgers, formula files
and solver logs are generated under `runs/` when reproducing the calculation;
they are not mixed into the source tree.
