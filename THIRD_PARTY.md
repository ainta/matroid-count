# Sources and attribution

This repository combines new orchestration, modular-cut counting, symmetry
accounting and audit code with the following earlier implementations.

## Parent generator

The runtime source subset in `vendor/matroid-generator/` is copied without
changes from [gmou3/matroid-generator](https://github.com/gmou3/matroid-generator),
commit `60645ae024e831fba3ebd35b2388515b0304140a`. Its GPL-3.0 license is retained
in [LICENSE](vendor/matroid-generator/LICENSE). Unused upstream commands, tests
and generated outputs are omitted; the root Makefile builds only `build/IC`.
The generator was not authored as part of this project.

## Sparse-paving implementation

`augment_sparse.cpp`, `split_count.cpp`, `small_extensions.hpp` and
`burnside_sparse.cpp` originate in the supplied `matroid_fast_algorithms.zip`.
They have been formatted for readability. The persistent sparse-paving runner
was developed during this computation and now shares CPU discovery with the
general worker runner. No licensing grant beyond the supplied source is implied.

## Downloaded tools

- [Ganak v2.6.4](https://github.com/meelgroup/ganak): exact model counting. The
  Linux x86-64 archive and executable are checksum-pinned in
  [`scripts/setup.py`](scripts/setup.py). The executable is downloaded locally,
  not committed to this repository.
- [Nauty 2.9.3](https://users.cecs.anu.edu.au/~bdm/nauty/): independent canonical
  labeling and automorphism checks, Apache-2.0. Its source archive is
  checksum-pinned, downloaded into `deps/` and built with thread-local storage.
  Citation: McKay–Piperno, *Practical Graph Isomorphism, II*, Journal of Symbolic
  Computation 60 (2014), 94–112, DOI
  [10.1016/j.jsc.2013.09.003](https://doi.org/10.1016/j.jsc.2013.09.003).

## Reference data

The [Mayhew–Royle catalogue](https://zenodo.org/records/6825419) is used only for
the optional independent comparison. It is neither bundled nor read by the
production counter. The source of each published benchmark is documented in
[`docs/validation.md`](docs/validation.md).
