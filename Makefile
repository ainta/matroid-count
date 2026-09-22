CXX ?= g++
CXXFLAGS ?= -O3 -march=native -std=c++17
PYTHON ?= python3

all: build/count_extensions build/colex_to_rank vendor/matroid-generator/build/IC

build:
	mkdir -p $@

build/count_extensions: src/count_extensions.cpp | build
	$(CXX) $(CXXFLAGS) $< -o $@

build/colex_to_rank: src/colex_to_rank.cpp | build
	$(CXX) $(CXXFLAGS) $< -o $@

vendor/matroid-generator/build/IC: $(wildcard vendor/matroid-generator/src/*)
	$(MAKE) -C vendor/matroid-generator build/IC

deps/nauty2_9_3/nauty.a:
	@test -f deps/nauty2_9_3/configure || (echo 'Run python3 scripts/setup.py --audit first'; exit 1)
	cd deps/nauty2_9_3 && ./configure --enable-tls && $(MAKE) -j4 nauty.a

build/rank_audit: src/rank_audit.cpp deps/nauty2_9_3/nauty.a | build
	$(CXX) $(CXXFLAGS) -fopenmp -Ideps/nauty2_9_3 $< deps/nauty2_9_3/nauty.a -o $@

audit: build/rank_audit

test: all audit
	$(PYTHON) tests/smoke.py

verify:
	$(PYTHON) scripts/verify_results.py

.PHONY: all audit test verify
