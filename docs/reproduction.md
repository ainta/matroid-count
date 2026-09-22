# Reproduce the count

Run these commands from the repository root on Linux x86-64. You need
Python 3.10 or newer, GCC with C++17 support, Make, and Boost headers.
On Ubuntu, install g++, make, libboost-dev, and python3.

## Build and test

~~~bash
python3 scripts/setup.py --audit
make -j4
make audit
make test
make verify
~~~

The setup script downloads checksum-pinned Ganak for exact model counting.
The optional audit target also downloads nauty. The nine-element parent
generator is included as pinned source under vendor/.

The default C++ flags include -march=native. Build on the machine that
will run the program. The test suite generates parents through eight
elements, audits their rank functions and isomorphism classes, and
reproduces four published rank counts.

## Count ten-element matroids

~~~bash
python3 scripts/generate_parents.py --through 9 --jobs 64 \
    --out runs/n10/parents
python3 -S scripts/count.py --parents runs/n10/parents \
    --workdir runs/n10/count --jobs 64
python3 scripts/verify_results.py --run runs/n10/count
~~~

Set --jobs to the number of available physical cores. The generator
creates the nine-element parents from the empty matroid. The counter
uses the same modular-cut worker for all parents and runs exact model
counting for the cycle types without a fixed point. It writes the total
to runs/n10/count/result.json and the fixed counts to each
rank*/result.json. The verifier compares all 126 fixed counts, the rank
totals, and the final count with the recorded results.

The counter prints parent progress to standard error. The generated
rank files, formulas, and solver input remain under runs/, which Git
ignores. An unfinished subproblem stops the run with an error. This
short driver does not checkpoint individual parents; restart the
counting command after a failure.

The recorded 64-worker run took about ten minutes after parent
generation on two AMD EPYC 9354 CPUs. Parent generation took about
four seconds. Actual time depends on CPU speed and the exact model
counter. Each exact model-counting process can use up to 1 GiB of cache.

## Audit the generated parents

The counting command does not require a downloaded catalogue. To check
the generated parents independently with nauty, run:

~~~bash
python3 scripts/audit.py runs/n10/parents/all_ranklines.txt \
    --out runs/n10/audit --jobs 64
~~~

The audit tests rank axioms, detects isomorphic duplicates, checks
duality, and records one canonical rank array per class. It should
find 385,370 matroids through nine elements, including 383,172 with
exactly nine elements.

For an optional comparison with the complete public catalogue:

~~~bash
python3 scripts/setup.py --catalogue
./build/rank_audit data/matroids09_rankLine runs/n10/reference.tsv 64
python3 scripts/compare_catalogues.py \
    --generated runs/n10/audit/canonical.tsv \
    --reference runs/n10/reference.tsv \
    --out runs/n10/catalogue-comparison.json
~~~

This comparison checks the complete canonical rank arrays and
automorphism orders. The reference catalogue is not an input to the
counting command.
