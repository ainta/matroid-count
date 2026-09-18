// Independent rank-axiom and isomorphism audit; no counting-worker code reused.
// nauty sees the two-colored element/hyperplane incidence graph.
#include "nauty.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <fstream>
#include <iostream>
#include <numeric>
#include <omp.h>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;

struct Canon {
    string ranks;
    unsigned aut;
};
Canon canonical(const string &ranks, int n) {
    if (!n)
        return {"0", 1};
    int full = (1 << n) - 1, r = ranks.back() - '0';
    vector<int> hyperplanes;
    for (int s = 0; s <= full; ++s)
        if (ranks[s] - '0' == r - 1) {
            bool flat = true;
            for (int i = 0; i < n; ++i)
                if (!(s >> i & 1) && ranks[s | 1 << i] == ranks[s]) {
                    flat = false;
                    break;
                }
            if (flat)
                hyperplanes.push_back(s);
        }
    int vertices = n + hyperplanes.size(), m = SETWORDSNEEDED(vertices);
    vector<graph> g(vertices * m), cg(vertices * m);
    vector<int> lab(vertices), ptn(vertices, 1), orbits(vertices);
    iota(lab.begin(), lab.end(), 0);
    ptn[n - 1] = ptn.back() = 0;
    for (size_t h = 0; h < hyperplanes.size(); ++h)
        for (int i = 0; i < n; ++i)
            if (hyperplanes[h] >> i & 1)
                ADDONEEDGE(g.data(), i, n + h, m);
    DEFAULTOPTIONS_GRAPH(options);
    options.getcanon = TRUE;
    options.defaultptn = FALSE;
    statsblk stats;
    densenauty(g.data(), lab.data(), ptn.data(), orbits.data(), &options, &stats, m, vertices,
               cg.data());
    if (stats.errstatus)
        throw runtime_error("nauty failure");
    double group = stats.grpsize1 * pow(10., stats.grpsize2);
    unsigned aut = llround(group), fac = 1;
    for (int i = 2; i <= n; ++i)
        fac *= i;
    if (!aut || fac % aut || abs(group - aut) > 0.0001)
        throw runtime_error("invalid group size");
    vector<int> images(1 << n);
    string out(ranks.size(), '0');
    for (int i = 0; i < n; ++i)
        if (lab[i] >= n)
            throw runtime_error("point color lost");
    for (int s = 1; s <= full; ++s) {
        int i = __builtin_ctz(unsigned(s));
        images[s] = images[s & (s - 1)] | (1 << lab[i]);
    }
    for (int s = 0; s <= full; ++s)
        out[s] = ranks[images[s]];
    return {out, aut};
}

void rank_axioms(const string &ranks, int n) {
    int full = (1 << n) - 1;
    if (ranks[0] != '0')
        throw runtime_error("empty-set rank nonzero");
    for (int s = 0; s <= full; ++s) {
        int r = ranks[s] - '0';
        if (r < 0 || r > __builtin_popcount(unsigned(s)))
            throw runtime_error("rank bound violated");
        for (int i = 0; i < n; ++i)
            if (!(s >> i & 1)) {
                int si = s | 1 << i, increment = ranks[si] - ranks[s];
                if (increment < 0 || increment > 1)
                    throw runtime_error("rank increment violated");
                for (int j = i + 1; j < n; ++j)
                    if (!(s >> j & 1))
                        if (int(ranks[si]) + ranks[s | 1 << j] < int(ranks[s]) + ranks[si | 1 << j])
                            throw runtime_error("local submodularity violated");
            }
    }
    // Reconstruct every rank independently as the largest independent subset.
    vector<int> recovered(1 << n);
    for (int s = 0; s <= full; ++s) {
        int k = __builtin_popcount(unsigned(s));
        if (ranks[s] - '0' == k)
            recovered[s] = k;
    }
    for (int i = 0; i < n; ++i)
        for (int s = 0; s <= full; ++s)
            if (s >> i & 1)
                recovered[s] = max(recovered[s], recovered[s ^ (1 << i)]);
    for (int s = 0; s <= full; ++s)
        if (recovered[s] != ranks[s] - '0')
            throw runtime_error("rank reconstruction failed");
}

int main(int argc, char **argv) {
    if (argc != 4) {
        cerr << "usage: rank_audit input_ranklines output_tsv threads\n";
        return 2;
    }
    ifstream in(argv[1]);
    if (!in) {
        cerr << "input unavailable\n";
        return 2;
    }
    vector<string> lines;
    string line;
    while (getline(in, line))
        lines.push_back(line == "NULL" ? "0" : line);
    vector<string> output(lines.size()), errors(lines.size());
    atomic<unsigned long long> bounds(0), increments(0), squares(0);
    double start = omp_get_wtime();
    omp_set_num_threads(stoi(argv[3]));
    nauty_check(WORDSIZE, 1, 1, NAUTYVERSIONID);
#pragma omp parallel for schedule(dynamic, 32)
    for (size_t row = 0; row < lines.size(); ++row)
        try {
            const auto &ranks = lines[row];
            int n = 0;
            while (n < 10 && (1u << n) < ranks.size())
                ++n;
            if (n > 9 || (1u << n) != ranks.size())
                throw runtime_error("invalid rankline length");
            rank_axioms(ranks, n);
            int full = (1 << n) - 1, r = ranks.back() - '0';
            string dual(ranks.size(), '0');
            for (int s = 0; s <= full; ++s)
                dual[s] = __builtin_popcount(unsigned(s)) + ranks[full ^ s] - r;
            rank_axioms(dual, n);
            auto a = canonical(ranks, n), b = canonical(dual, n);
            if (a.aut != b.aut)
                throw runtime_error("dual group order mismatch");
            // Relabel every entry by a deterministic changing permutation.
            vector<int> p(n), image(1 << n);
            iota(p.begin(), p.end(), 0);
            if (n) {
                rotate(p.begin(), p.begin() + (row % n), p.end());
                if (row & 1)
                    reverse(p.begin(), p.end());
            }
            string moved(ranks.size(), '0');
            for (int s = 1; s <= full; ++s) {
                int i = __builtin_ctz(unsigned(s));
                image[s] = image[s & (s - 1)] | (1 << p[i]);
            }
            for (int s = 0; s <= full; ++s)
                moved[s] = ranks[image[s]];
            auto c = canonical(moved, n);
            if (c.ranks != a.ranks || c.aut != a.aut)
                throw runtime_error("canonical relabeling mismatch");
            output[row] = to_string(row) + "\t" + to_string(n) + "\t" + to_string(r) + "\t" +
                          to_string(a.aut) + "\t" + a.ranks + "\t" + b.ranks + "\n";
            bounds += ranks.size();
            if (n)
                increments += (uint64_t(n) << (n - 1));
            if (n >= 2)
                squares += (uint64_t(n * (n - 1) / 2) << (n - 2));
        } catch (const exception &e) {
            errors[row] = e.what();
        }
    unsigned failures = 0;
    for (size_t i = 0; i < errors.size(); ++i)
        if (!errors[i].empty()) {
            cerr << "row " << i << ": " << errors[i] << "\n";
            ++failures;
        }
    if (failures)
        return 1;
    ofstream out(argv[2]);
    for (auto &s : output)
        out << s;
    if (!out)
        throw runtime_error("output write failed");
    cerr << "{\"status\":\"passed\",\"records\":" << lines.size() << ",\"rank_bounds\":" << bounds
         << ",\"rank_increments\":" << increments << ",\"submodular_squares\":" << squares
         << ",\"dual_checks\":" << lines.size() << ",\"relabeling_checks\":" << lines.size()
         << ",\"seconds\":" << omp_get_wtime() - start << ",\"nauty\":\"" << NAUTYVERSION
         << "\"}\n";
}
