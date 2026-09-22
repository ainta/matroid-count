# Sources and attribution

The counting route uses the following third-party code and data.

## Parent generator

The runtime source subset in `vendor/matroid-generator/` is copied without
changes from [gmou3/matroid-generator](https://github.com/gmou3/matroid-generator),
commit `60645ae024e831fba3ebd35b2388515b0304140a`. Its GPL-3.0 license is retained
in [LICENSE](vendor/matroid-generator/LICENSE). The included source supports the
`build/IC` target used by the root Makefile.

## Downloaded tools

- [Ganak v2.6.4](https://github.com/meelgroup/ganak): exact model counting. The
  Linux x86-64 archive and executable are checksum-pinned in
  [`scripts/setup.py`](scripts/setup.py) and downloaded into `deps/`.
- [Nauty 2.9.3](https://users.cecs.anu.edu.au/~bdm/nauty/): independent canonical
  labeling and automorphism checks, Apache-2.0. Its source archive is
  checksum-pinned, downloaded into `deps/` and built with thread-local storage.
  Citation: McKay–Piperno, *Practical Graph Isomorphism, II*, Journal of Symbolic
  Computation 60 (2014), 94–112, DOI
  [10.1016/j.jsc.2013.09.003](https://doi.org/10.1016/j.jsc.2013.09.003).

## Reference data

The [Mayhew–Royle catalogue](https://zenodo.org/records/6825419) supplies the
optional external comparison. Published benchmark sources are listed in
[`docs/validation.md`](docs/validation.md).
