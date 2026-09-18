// Isomorph-free sparse-paving generation by canonical deletion.
// Every symmetry tie is resolved by exact permutation search, not by hashes.
#include <bits/stdc++.h>
using namespace std;
using Perm = array<uint8_t, 12>;
uint64_t mix64(uint64_t x) {
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}
template <int W> struct Bits {
    array<uint64_t, W> a{};
    bool operator==(const Bits &b) const {
        return a == b.a;
    }
    bool operator<(const Bits &b) const {
        for (int i = W - 1; i >= 0; i--)
            if (a[i] != b.a[i])
                return a[i] < b.a[i];
        return false;
    }
    bool any() const {
        for (auto x : a)
            if (x)
                return true;
        return false;
    }
    int first() const {
        for (int i = 0; i < W; i++)
            if (a[i])
                return 64 * i + __builtin_ctzll(a[i]);
        return -1;
    }
    void set(int i) {
        a[i / 64] |= 1ULL << (i % 64);
    }
    void reset(int i) {
        a[i / 64] &= ~(1ULL << (i % 64));
    }
    Bits minus(const Bits &b) const {
        Bits c;
        for (int i = 0; i < W; i++)
            c.a[i] = a[i] & ~b.a[i];
        return c;
    }
};
template <int W> struct Generator {
    using B = Bits<W>;
    int n, r, V;
    vector<unsigned> sub;
    vector<int> idx;
    vector<B> adj;
    B full;
    int degree[12] = {}, pairs[12][12] = {};
    vector<int> family;
    uint64_t total = 0, candidates = 0, canon_calls = 0, unique_accepts = 0, perm_evals = 0;
    __uint128_t labeled = 0;
    uint64_t fac = 1;
    vector<uint64_t> layers;
    double limit = 60;
    chrono::steady_clock::time_point start;
    ostream *out = nullptr;
    Generator(int nn, int rr) : n(nn), r(rr), idx(1 << nn, -1) {
        auto gen = [&](auto &&self, int f, int left, unsigned s) -> void {
            if (!left) {
                idx[s] = sub.size();
                sub.push_back(s);
                return;
            }
            for (int i = f; i <= n - left; i++)
                self(self, i + 1, left - 1, s | (1u << i));
        };
        gen(gen, 0, r, 0);
        V = sub.size();
        adj.resize(V);
        for (int i = 0; i < V; i++) {
            full.set(i);
            adj[i].set(i);
            for (int j = 0; j < V; j++)
                if (__builtin_popcount(sub[i] ^ sub[j]) == 2)
                    adj[i].set(j);
        }
        for (int i = 2; i <= n; i++)
            fac *= i;
        layers.resize(V + 1);
    }
    unsigned image(unsigned z, const Perm &p) const {
        unsigned t = 0;
        while (z) {
            int i = __builtin_ctz(z);
            z &= z - 1;
            t |= 1u << p[i];
        }
        return t;
    }
    void push(int v) {
        family.push_back(v);
        unsigned z = sub[v];
        for (int i = 0; i < n; i++)
            if (z >> i & 1) {
                degree[i]++;
                for (int j = i + 1; j < n; j++)
                    if (z >> j & 1) {
                        pairs[i][j]++;
                        pairs[j][i]++;
                    }
            }
    }
    void pop() {
        unsigned z = sub[family.back()];
        family.pop_back();
        for (int i = 0; i < n; i++)
            if (z >> i & 1) {
                degree[i]--;
                for (int j = i + 1; j < n; j++)
                    if (z >> j & 1) {
                        pairs[i][j]--;
                        pairs[j][i]--;
                    }
            }
    }
    uint64_t degree_sig(int v) const {
        int d[12], k = 0;
        unsigned z = sub[v];
        while (z) {
            int i = __builtin_ctz(z);
            z &= z - 1;
            d[k++] = degree[i];
        }
        sort(d, d + k);
        uint64_t h = 0;
        for (int i = 0; i < k; i++)
            h = (h << 7) | d[i];
        return h;
    }
    // A coarse invariant only. Collisions can increase work but never affect correctness.
    uint64_t refined_sig(int v, const uint64_t *colors) const {
        uint64_t a[12];
        int k = 0;
        unsigned z = sub[v];
        while (z) {
            int i = __builtin_ctz(z);
            z &= z - 1;
            a[k++] = colors[i];
        }
        sort(a, a + k);
        uint64_t h = 0;
        for (int i = 0; i < k; i++)
            h = mix64(h ^ a[i]);
        return h;
    }
    vector<int> deletions(int added) {
        uint64_t s = degree_sig(added);
        vector<int> tied;
        for (int v : family) {
            auto z = degree_sig(v);
            if (z > s)
                return {};
            if (z == s)
                tied.push_back(v);
        }
        if (tied.size() == 1)
            return tied;
        uint64_t colors[12];
        for (int i = 0; i < n; i++) {
            uint64_t a[12];
            int k = 0;
            for (int j = 0; j < n; j++)
                if (i != j)
                    a[k++] = (uint64_t(degree[j]) << 16) | pairs[i][j];
            sort(a, a + k);
            uint64_t h = degree[i];
            for (int j = 0; j < k; j++)
                h = mix64(h ^ a[j]);
            colors[i] = h;
        }
        s = refined_sig(added, colors);
        vector<int> fine;
        for (int v : tied) {
            auto z = refined_sig(v, colors);
            if (z > s)
                return {};
            if (z == s)
                fine.push_back(v);
        }
        return fine;
    }
    // Return all automorphisms only when the canonical deletion test accepts.
    bool exact_test(int added, const vector<int> &ties, vector<Perm> &automorphisms) {
        canon_calls++;
        array<array<int, 25>, 12> sig{};
        for (int i = 0; i < n; i++) {
            sig[i][0] = degree[i];
            array<pair<int, int>, 12> a;
            int k = 0;
            for (int j = 0; j < n; j++)
                if (i != j)
                    a[k++] = {degree[j], pairs[i][j]};
            sort(a.begin(), a.begin() + k);
            for (int j = 0; j < k; j++) {
                sig[i][2 * j + 1] = a[j].first;
                sig[i][2 * j + 2] = a[j].second;
            }
        }
        vector<int> ord(n);
        iota(ord.begin(), ord.end(), 0);
        sort(ord.begin(), ord.end(),
             [&](int i, int j) { return sig[i] != sig[j] ? sig[i] < sig[j] : i < j; });
        vector<pair<int, int>> groups;
        for (int i = 0; i < n;) {
            int j = i + 1;
            while (j < n && sig[ord[i]] == sig[ord[j]])
                j++;
            groups.push_back({i, j});
            i = j;
        }
        B best;
        for (auto &x : best.a)
            x = ~0ULL;
        vector<Perm> maps;
        bool accept = false;
        auto eval = [&]() {
            perm_evals++;
            Perm p{};
            for (int i = 0; i < n; i++)
                p[ord[i]] = i;
            B b;
            for (int v : family)
                b.set(idx[image(sub[v], p)]);
            if (best < b)
                return;
            if (b < best) {
                best = b;
                maps.clear();
                accept = false;
            }
            maps.push_back(p);
            int smallest = V;
            for (int v : ties)
                smallest = min(smallest, idx[image(sub[v], p)]);
            if (idx[image(sub[added], p)] == smallest)
                accept = true;
        };

        // Individualize/refine the full block-incidence structure. Pair signatures
        // alone do not distinguish regular designs; incidence refinement does.
        using Colors = array<int, 12>;
        auto refine = [&](Colors color) {
            for (;;) {
                array<array<uint64_t, 130>, 12> keys{};
                int lens[12] = {};
                for (int i = 0; i < n; i++) {
                    keys[i][0] = color[i];
                    lens[i] = 1;
                }
                for (int v : family) {
                    int cc[12], cnt = 0;
                    unsigned z = sub[v];
                    while (z) {
                        int i = __builtin_ctz(z);
                        z &= z - 1;
                        cc[cnt++] = color[i];
                    }
                    sort(cc, cc + cnt);
                    uint64_t key = 0;
                    for (int j = 0; j < cnt; j++)
                        key = (key << 4) | cc[j];
                    z = sub[v];
                    while (z) {
                        int i = __builtin_ctz(z);
                        z &= z - 1;
                        keys[i][lens[i]++] = key;
                    }
                }
                for (int i = 0; i < n; i++)
                    sort(keys[i].begin() + 1, keys[i].begin() + lens[i]);
                array<int, 12> order{};
                iota(order.begin(), order.begin() + n, 0);
                auto less = [&](int i, int j) {
                    if (keys[i][0] != keys[j][0])
                        return keys[i][0] < keys[j][0];
                    if (lens[i] != lens[j])
                        return lens[i] < lens[j];
                    return lexicographical_compare(keys[i].begin() + 1, keys[i].begin() + lens[i],
                                                   keys[j].begin() + 1, keys[j].begin() + lens[j]);
                };
                sort(order.begin(), order.begin() + n, less);
                Colors next{};
                int c = 0;
                for (int j = 0; j < n; j++) {
                    if (j && less(order[j - 1], order[j]))
                        c++;
                    next[order[j]] = c;
                }
                if (next == color)
                    return color;
                color = next;
            }
        };
        Colors initial{};
        for (int g = 0; g < (int)groups.size(); g++) {
            auto [a, b] = groups[g];
            for (int j = a; j < b; j++)
                initial[ord[j]] = g;
        }
        auto search = [&](auto &&self, Colors color) -> void {
            color = refine(color);
            int counts[12] = {};
            for (int i = 0; i < n; i++)
                counts[color[i]]++;
            int c = -1;
            for (int j = 0; j < n; j++)
                if (counts[j] > 1) {
                    c = j;
                    break;
                }
            if (c < 0) {
                for (int i = 0; i < n; i++)
                    ord[color[i]] = i;
                eval();
                return;
            }
            for (int v = 0; v < n; v++)
                if (color[v] == c) {
                    Colors next = color;
                    for (int i = 0; i < n; i++)
                        if (color[i] > c || (color[i] == c && i != v))
                            next[i]++;
                    self(self, next);
                }
        };
        search(search, initial);

        if (!accept)
            return false;
        if (maps.size() == 1) {
            automorphisms.clear();
            return true;
        }
        Perm inv{};
        for (int i = 0; i < n; i++)
            inv[maps[0][i]] = i;
        automorphisms.resize(maps.size());
        for (size_t j = 0; j < maps.size(); j++)
            for (int i = 0; i < n; i++)
                automorphisms[j][i] = inv[maps[j][i]];
        return true;
    }
    static string decimal(__uint128_t x) {
        if (!x)
            return "0";
        string s;
        while (x) {
            s += char('0' + x % 10);
            x /= 10;
        }
        reverse(s.begin(), s.end());
        return s;
    }
    void record(B s, const vector<Perm> &aut) {
        uint64_t a = aut.empty() ? 1 : aut.size();
        if (total == UINT64_MAX || labeled > ~__uint128_t(0) - fac / a)
            throw runtime_error("count capacity exceeded");
        total++;
        layers[family.size()]++;
        labeled += fac / a;
        if (out) {
            *out << family.size();
            if constexpr (W == 1)
                *out << " 0";
            for (int i = W - 1; i >= 0; i--)
                *out << ' ' << s.a[i];
            *out << ' ' << a << '\n';
        }
    }
    void dfs(B s, B allowed, const vector<Perm> &aut) {
        record(s, aut);
        B seen;
        while (allowed.any()) {
            int v = allowed.first();
            allowed.reset(v);
            if (seen.a[v / 64] >> (v % 64) & 1)
                continue;
            if (!aut.empty())
                for (const auto &p : aut)
                    seen.set(idx[image(sub[v], p)]);
            if ((++candidates & 16383) == 0 &&
                chrono::duration<double>(chrono::steady_clock::now() - start).count() > limit)
                throw runtime_error("timeout");
            push(v);
            auto ties = deletions(v);
            if (ties.empty()) {
                pop();
                continue;
            }
            vector<Perm> childaut;
            bool accepted;
            if (ties.size() == 1) {
                unique_accepts++;
                accepted = true;
                if (!aut.empty()) {
                    for (const auto &p : aut)
                        if (image(sub[v], p) == sub[v])
                            childaut.push_back(p);
                    if (childaut.size() == 1)
                        childaut.clear();
                }
            } else
                accepted = exact_test(v, ties, childaut);
            if (accepted) {
                B child = s;
                child.set(v);
                B next = full;
                for (int x : family)
                    next = next.minus(adj[x]);
                dfs(child, next, childaut);
            }
            pop();
        }
    }
    void run() {
        start = chrono::steady_clock::now();
        total = 1;
        labeled = 1;
        layers[0] = 1;
        if (out) {
            *out << 0;
            if constexpr (W == 1)
                *out << " 0";
            for (int i = 0; i < W; i++)
                *out << " 0";
            *out << ' ' << fac << '\n';
        }
        push(0);
        vector<Perm> aut;
        exact_test(0, {0}, aut);
        B s;
        s.set(0);
        dfs(s, full.minus(adj[0]), aut);
        pop();
    }
    void summary(string status) {
        cout << "{\"status\":\"" << status << "\",\"n\":" << n << ",\"r\":" << r
             << ",\"unlabeled\":" << total << ",\"labeled\":\"" << decimal(labeled)
             << "\",\"candidates\":" << candidates << ",\"canonical_tests\":" << canon_calls
             << ",\"unique_deletion_accepts\":" << unique_accepts
             << ",\"permutations\":" << perm_evals << ",\"seconds\":"
             << chrono::duration<double>(chrono::steady_clock::now() - start).count()
             << ",\"layers\":[";
        for (size_t k = 0; k < layers.size(); k++) {
            if (k)
                cout << ',';
            cout << layers[k];
            if (k + 1 >= layers.size() ||
                accumulate(layers.begin() + k + 1, layers.end(), uint64_t(0)) == 0)
                break;
        }
        cout << "]}\n";
    }
};
template <int W> int run(int n, int r, double limit, const char *path) {
    Generator<W> g(n, r);
    g.limit = limit;
    ofstream f;
    if (path) {
        f.open(path);
        if (!f) {
            cerr << "cannot open output\n";
            return 2;
        }
        g.out = &f;
    }
    try {
        g.run();
        g.summary("complete");
        return 0;
    } catch (exception &e) {
        g.summary("partial");
        return 3;
    }
}
int main(int ac, char **av) {
    try {
        if (ac < 3) {
            cerr << "usage: augment_sparse n r [seconds=60] [output.tsv]\n";
            return 2;
        }
        int n = stoi(av[1]), r = stoi(av[2]);
        double limit = ac > 3 ? stod(av[3]) : 60;
        if (n < 2 || n > 11 || r < 1 || r >= n)
            throw runtime_error("supported: 2<=n<=11 and 0<r<n");
        int V = 1;
        for (int i = 1; i <= r; i++)
            V = V * (n - i + 1) / i;
        const char *path = ac > 4 ? av[4] : nullptr;
        if (V <= 64)
            return run<1>(n, r, limit, path);
        if (V <= 128)
            return run<2>(n, r, limit, path);
        if (V <= 256)
            return run<4>(n, r, limit, path);
        return run<8>(n, r, limit, path);
    } catch (exception &e) {
        cerr << e.what() << '\n';
        return 2;
    }
}
