// Exact labeled sparse-paving count by a distinguished-element split.
// Input: n rank orbit_file; orbit records are k high64 low64 automorphism_order.
#include <bits/stdc++.h>
#include <boost/multiprecision/cpp_int.hpp>
using namespace std;
using U = __uint128_t;
using boost::multiprecision::cpp_int;
int pc(U a) {
    return __builtin_popcountll((uint64_t)a) + __builtin_popcountll((uint64_t)(a >> 64));
}
int first(U a) {
    return (uint64_t)a ? __builtin_ctzll((uint64_t)a) : 64 + __builtin_ctzll((uint64_t)(a >> 64));
}
string dec(U a) {
    if (!a)
        return "0";
    string s;
    while (a) {
        s += char('0' + a % 10);
        a /= 10;
    }
    reverse(s.begin(), s.end());
    return s;
}
struct Hash {
    size_t operator()(U a) const {
        uint64_t x = (uint64_t)a ^ ((uint64_t)(a >> 64) * 0x9e3779b97f4a7c15ULL);
        x ^= x >> 30;
        x *= 0xbf58476d1ce4e5b9ULL;
        x ^= x >> 27;
        x *= 0x94d049bb133111ebULL;
        return x ^ (x >> 31);
    }
};
struct Cache {
    struct Entry {
        U key = 0, value = 0;
    };
    vector<Entry> a;
    size_t mask = 0, used = 0;
    void reserve(size_t cap) {
        size_t n = 1;
        while (n < max(size_t(1024), cap))
            n *= 2;
        a.resize(n);
        mask = n - 1;
    }
    bool get(U s, U &v) {
        size_t h = Hash{}(s)&mask;
        for (int j = 0; j < 4; j++) {
            auto &e = a[(h + j) & mask];
            if (e.key == s) {
                v = e.value;
                return true;
            }
            if (!e.key)
                return false;
        }
        return false;
    }
    void emplace(U s, U v) {
        size_t h = Hash{}(s)&mask;
        for (int j = 0; j < 4; j++) {
            auto &e = a[(h + j) & mask];
            if (e.key == s) {
                e.value = v;
                return;
            }
            if (!e.key) {
                e = {s, v};
                used++;
                return;
            }
        }
        a[h] = {s, v};
    }
    size_t size() const {
        return used;
    }
};
struct Counter {
    vector<U> adj;
    Cache memo;
    uint64_t calls = 0, hits = 0;
    size_t cap = 2000000;
    double limit = 30;
    chrono::steady_clock::time_point start;
    U solve(U s) {
        if ((++calls & 65535) == 0 &&
            chrono::duration<double>(chrono::steady_clock::now() - start).count() > limit)
            throw runtime_error("timeout");
        if (!s)
            return 1;
        U found;
        if (memo.get(s, found)) {
            ++hits;
            return found;
        }
        U orig = s, scan = s;
        int maxdeg = 0, vmax = -1, isolated = 0;
        while (scan) {
            int v = first(scan);
            scan &= scan - 1;
            int d = pc(adj[v] & s);
            if (!d) {
                s &= ~(U(1) << v);
                isolated++;
            } else if (d > maxdeg) {
                maxdeg = d;
                vmax = v;
            }
        }
        if (!s)
            return U(1) << isolated;
        U ans;
        // Component splitting is worthwhile for small or low-degree residuals.
        U comp = s;
        if (pc(s) < 45 || maxdeg < 5) {
            comp = U(1) << vmax;
            U front = comp;
            while (front) {
                int v = first(front);
                front &= front - 1;
                U add = adj[v] & s & ~comp;
                comp |= add;
                front |= add;
            }
        }
        if (comp != s)
            ans = solve(comp) * solve(s & ~comp);
        else if (maxdeg <= 2) {
            int sz = pc(s);
            bool cycle = true;
            scan = s;
            while (scan) {
                int v = first(scan);
                scan &= scan - 1;
                if (pc(adj[v] & s) != 2) {
                    cycle = false;
                    break;
                }
            }
            U f[130];
            f[0] = 0;
            f[1] = 1;
            for (int i = 2; i <= sz + 2; i++)
                f[i] = f[i - 1] + f[i - 2];
            ans = cycle ? f[sz - 1] + f[sz + 1] : f[sz + 2];
        } else {
            U ex = s & ~(U(1) << vmax);
            ans = solve(ex) + solve(ex & ~adj[vmax]);
        }
        ans <<= isolated;
        memo.emplace(orig, ans);
        return ans;
    }
};
vector<unsigned> subsets(int n, int r) {
    vector<unsigned> s;
    auto gen = [&](auto &&self, int p, int left, unsigned b) -> void {
        if (!left) {
            s.push_back(b);
            return;
        }
        for (int i = p; i <= n - left; i++)
            self(self, i + 1, left - 1, b | (1u << i));
    };
    gen(gen, 0, r, 0);
    return s;
}
#include "small_extensions.hpp"
int main(int ac, char **av) {
    try {
        if (ac < 4)
            throw runtime_error("usage: split_count n r orbit_file [seconds_per_root=30] [first=0] "
                                "[count=all] [cachecap=2000000] [complete_9_4_catalogue_for_IE]");
        int n = stoi(av[1]), r = stoi(av[2]);
        if (n < 3 || n > 10 || r < 2 || r >= n)
            throw runtime_error("unsupported parameters");
        auto A = subsets(n - 1, r - 1), B = subsets(n - 1, r);
        if (A.size() > 126 || B.size() > 126)
            throw runtime_error("mask limit");
        unique_ptr<SmallExtensions9> small;
        double precompute = 0;
        if (ac > 8) {
            if (n != 10 || r != 5)
                throw runtime_error("IE catalogue is for n=10 r=5 only");
            auto t = chrono::steady_clock::now();
            small = make_unique<SmallExtensions9>(av[8]);
            precompute = chrono::duration<double>(chrono::steady_clock::now() - t).count();
        }
        Counter c;
        if (ac > 4)
            c.limit = stod(av[4]);
        size_t skip = ac > 5 ? stoull(av[5]) : 0, take = ac > 6 ? stoull(av[6]) : SIZE_MAX;
        if (ac > 7)
            c.cap = stoull(av[7]);
        c.memo.reserve(c.cap);
        c.adj.resize(B.size());
        for (int i = 0; i < (int)B.size(); i++)
            for (int j = 0; j < (int)B.size(); j++)
                if (__builtin_popcount(B[i] ^ B[j]) == 2)
                    c.adj[i] |= U(1) << j;
        vector<U> forbid(A.size());
        for (int i = 0; i < (int)A.size(); i++)
            for (int j = 0; j < (int)B.size(); j++)
                if ((A[i] & B[j]) == A[i])
                    forbid[i] |= U(1) << j;
        U all = B.size() == 128 ? ~U(0) : (U(1) << B.size()) - 1;
        uint64_t factorial = 1;
        for (int i = 2; i < n; i++)
            factorial *= i;
        ifstream in(av[3]);
        if (!in)
            throw runtime_error("cannot open orbit file");
        int k;
        uint64_t hi, lo, aut;
        size_t row = 0, done = 0, timeouts = 0;
        cpp_int total = 0;
        auto t0 = chrono::steady_clock::now();
        while (in >> k >> hi >> lo >> aut) {
            size_t current = row++;
            if (current < skip || done >= take)
                continue;
            done++;
            if (!aut || factorial % aut)
                throw runtime_error("invalid automorphism order");
            U q = (U(hi) << 64) | lo, allowed = all;
            while (q) {
                int v = first(q);
                q &= q - 1;
                if (v >= (int)A.size())
                    throw runtime_error("invalid orbit bit");
                allowed &= ~forbid[v];
            }
            c.start = chrono::steady_clock::now();
            uint64_t oldcalls = c.calls;
            try {
                U z;
                if (small && k <= 5) {
                    U forbidden = 0;
                    for (int j = 0; j < (int)B.size(); j++)
                        if (!(allowed >> j & 1))
                            forbidden |= U(1) << small->index[B[j] ^ 511];
                    z = small->avoiding(forbidden);
                } else
                    z = c.solve(allowed);
                cpp_int contribution(dec(z));
                contribution *= factorial / aut;
                total += contribution;
                cout << "{\"row\":" << current << ",\"k\":" << k << ",\"vertices\":" << pc(allowed)
                     << ",\"status\":\"complete\",\"count\":\"" << dec(z)
                     << "\",\"weight\":" << factorial / aut;
            } catch (const runtime_error &) {
                timeouts++;
                cout << "{\"row\":" << current << ",\"k\":" << k << ",\"vertices\":" << pc(allowed)
                     << ",\"status\":\"timeout\"";
            }
            cout << ",\"calls\":" << c.calls - oldcalls << ",\"seconds\":"
                 << chrono::duration<double>(chrono::steady_clock::now() - c.start).count() << "}"
                 << endl;
        }
        cerr << "{\"status\":\""
             << (timeouts ? "partial" : (skip == 0 && done == row ? "complete" : "subset"))
             << "\",\"total\":\"" << total << "\",\"precompute_seconds\":" << precompute
             << ",\"roots\":" << done << ",\"timeouts\":" << timeouts << ",\"calls\":" << c.calls
             << ",\"hits\":" << c.hits << ",\"cache\":" << c.memo.size() << ",\"seconds\":"
             << chrono::duration<double>(chrono::steady_clock::now() - t0).count() << "}" << endl;
        return timeouts ? 3 : 0;
    } catch (exception &e) {
        cerr << e.what() << "\n";
        return 2;
    }
}
