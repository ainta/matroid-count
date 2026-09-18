CXX ?= g++
CXXFLAGS ?= -O3 -march=native -std=c++17
PYTHON ?= python3
PROGRAMS = augment_sparse split_count burnside_sparse extension_worker sparse_terms colex_to_rank
BINARIES = $(addprefix build/,$(PROGRAMS))
KERNEL = src/split_count.cpp src/small_extensions.hpp

all: $(BINARIES) vendor/matroid-generator/build/IC

build:
	mkdir -p $@

build/%: src/%.cpp | build
	$(CXX) $(CXXFLAGS) $< -o $@

build/split_count build/burnside_sparse build/extension_worker build/sparse_terms: $(KERNEL)

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

.PHONY: all audit test
