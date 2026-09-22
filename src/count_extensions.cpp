// Count matroid extensions through invariant modular cuts.
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
struct Counter {
    vector<U> adj;
    unordered_map<U, U, Hash> memo;
    deque<U> fifo;
    uint64_t calls = 0;
    size_t cap = 32768;
    double limit = 30;
    chrono::steady_clock::time_point start;
    U solve(U s) {
        if ((++calls & 65535) == 0 &&
            chrono::duration<double>(chrono::steady_clock::now() - start).count() > limit)
            throw runtime_error("timeout");
        if (!s)
            return 1;
        if (auto it = memo.find(s); it != memo.end()) return it->second;
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
        if (memo.size() == cap) { memo.erase(fifo.front()); fifo.pop_front(); }
        memo.emplace(orig, ans);
        fifo.push_back(orig);
        return ans;
    }
};
using Perm = array<uint8_t, 9>;
uint64_t encode(const Perm &p, int n) {
    uint64_t z = 0;
    for (int i = 0; i < n; i++)
        z |= uint64_t(p[i]) << (4 * i);
    return z;
}
string cycle_type(const Perm &p, int n) {
    vector<int> sizes;
    int seen = 0;
    for (int i = 0; i < n; i++)
        if (!(seen >> i & 1)) {
            int j = i, k = 0;
            do {
                seen |= 1 << j;
                j = p[j];
                k++;
            } while (j != i);
            sizes.push_back(k);
        }
    sort(sizes.begin(), sizes.end());
    string s;
    for (int k : sizes) {
        if (!s.empty())
            s += '.';
        s += to_string(k);
    }
    return s;
}
struct Matroid {
    int n, r, full;
    vector<int> rank, flats, frank, findex;
    explicit Matroid(const string &line) {
        n = 0;
        while ((1u << n) < line.size())
            n++;
        if (n > 9 || (1u << n) != line.size())
            throw runtime_error("invalid rankline length");
        full = (1 << n) - 1;
        for (char c : line) {
            if (c < '0' || c > '9')
                throw runtime_error("invalid rankline");
            rank.push_back(c - '0');
        }
        r = rank.back();
        if (rank[0] != 0 || r < 1 || r > n)
            throw runtime_error("unsupported rankline");
        findex.assign(1 << n, -1);
        for (int s = 0; s <= full; s++) {
            bool flat = true;
            for (int i = 0; i < n; i++)
                if (!(s >> i & 1) && rank[s | 1 << i] == rank[s]) {
                    flat = false;
                    break;
                }
            if (flat) {
                findex[s] = flats.size();
                flats.push_back(s);
                frank.push_back(rank[s]);
            }
        }
    }
    vector<Perm> automorphisms() const {
        // Exact backtracking: signatures only restrict candidates; every rank is checked.
        vector<array<int, 100>> signatures(n);
        for (int s = 1; s <= full; s++) {
            int key = 10 * __builtin_popcount(unsigned(s)) + rank[s];
            for (int i = 0; i < n; i++)
                if (s >> i & 1)
                    signatures[i][key]++;
        }
        vector<vector<int>> candidates(n);
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                if (signatures[i] == signatures[j])
                    candidates[i].push_back(j);
        vector<int> order(n);
        iota(order.begin(), order.end(), 0);
        stable_sort(order.begin(), order.end(),
                    [&](int a, int b) { return candidates[a].size() < candidates[b].size(); });
        vector<int> domain(1 << n), image(1 << n);
        for (int s = 1; s <= full; s++) {
            int b = __builtin_ctz(unsigned(s));
            domain[s] = domain[s & (s - 1)] | (1 << order[b]);
        }
        vector<Perm> group;
        Perm p{};
        auto rec = [&](auto &&self, int depth, int used) -> void {
            if (depth == n) {
                group.push_back(p);
                return;
            }
            int bit = 1 << depth;
            for (int v : candidates[order[depth]])
                if (!(used >> v & 1)) {
                    bool ok = true;
                    for (int s = 0; s < bit; s++) {
                        image[s | bit] = image[s] | (1 << v);
                        if (rank[domain[s | bit]] != rank[image[s | bit]]) {
                            ok = false;
                            break;
                        }
                    }
                    if (ok) {
                        p[order[depth]] = v;
                        self(self, depth + 1, used | (1 << v));
                    }
                }
        };
        rec(rec, 0, 0);
        return group;
    }
};
struct Conjugacy {
    Perm representative;
    size_t size;
};
vector<Conjugacy> conjugacy_classes(const vector<Perm> &group, int n) {
    unordered_map<uint64_t, size_t> lookup;
    lookup.reserve(group.size() * 2);
    for (size_t i = 0; i < group.size(); i++)
        lookup.emplace(encode(group[i], n), i);
    vector<bool> seen(group.size());
    vector<Conjugacy> result;
    for (size_t i = 0; i < group.size(); i++)
        if (!seen[i]) {
            size_t count = 0;
            for (const auto &h : group) {
                Perm conjugate{};
                for (int j = 0; j < n; j++)
                    conjugate[h[j]] = h[group[i][j]];
                auto it = lookup.find(encode(conjugate, n));
                if (it == lookup.end())
                    throw runtime_error("automorphism set not conjugation closed");
                if (!seen[it->second]) {
                    seen[it->second] = true;
                    count++;
                }
            }
            result.push_back({group[i], count});
        }
    size_t sum = 0;
    for (auto &c : result)
        sum += c.size;
    if (sum != group.size())
        throw runtime_error("class coverage failed");
    return result;
}

struct CutCounter {
    struct Clause {
        array<int, 3> lit{};
        int len = 0;
    };
    const Matroid &mat;
    int variables = 0;
    vector<int> fvar, vrank, hypvar, hypindex;
    vector<Clause> clauses;
    vector<vector<int>> occurrence;
    vector<int8_t> value;
    vector<int> trail;
    size_t head = 0;
    Counter graph;
    uint64_t nodes = 0, leaves = 0;
    chrono::steady_clock::time_point began;
    double seconds;

    CutCounter(const Matroid &m, const Perm &p, double limit, size_t cache)
        : mat(m), seconds(limit) {
        began = chrono::steady_clock::now();
        vector<int> images(1 << m.n);
        for (int s = 1; s <= m.full; s++) {
            int b = __builtin_ctz(unsigned(s));
            images[s] = images[s & (s - 1)] | (1 << p[b]);
        }
        fvar.assign(m.flats.size(), -1);
        for (size_t i = 0; i < m.flats.size(); i++)
            if (fvar[i] < 0) {
                int j = i;
                do {
                    fvar[j] = variables;
                    j = m.findex[images[m.flats[j]]];
                    if (j < 0)
                        throw runtime_error("permutation does not preserve flats");
                } while (j != int(i));
                vrank.push_back(m.frank[i]);
                variables++;
            }
        hypindex.assign(variables, -1);
        for (int v = 0; v < variables; v++)
            if (vrank[v] == m.r - 1) {
                hypindex[v] = hypvar.size();
                hypvar.push_back(v);
            }
        if (hypvar.size() > 126)
            throw runtime_error("hyperplane engine limit");
        graph.adj.resize(hypvar.size());
        graph.cap = max(cache, size_t(1024));
        graph.memo.reserve(graph.cap);
        graph.limit = seconds;
        graph.start = began;
        set<vector<int>> unique;
        auto add = [&](initializer_list<int> literals) {
            vector<int> c(literals);
            sort(c.begin(), c.end());
            c.erase(std::unique(c.begin(), c.end()), c.end());
            for (int x : c)
                if (binary_search(c.begin(), c.end(), -x))
                    return;
            unique.insert(c);
        };
        for (size_t i = 0; i < m.flats.size(); i++)
            for (size_t j = i + 1; j < m.flats.size(); j++) {
                int a = m.flats[i], b = m.flats[j], u = fvar[i], v = fvar[j];
                if ((a & b) == a)
                    add({-u - 1, v + 1});
                else if ((a & b) == b)
                    add({-v - 1, u + 1});
                else if (m.rank[a] + m.rank[b] == m.rank[a | b] + m.rank[a & b]) {
                    int w = fvar[m.findex[a & b]];
                    add({-u - 1, -v - 1, w + 1});
                }
                if (m.frank[i] == m.r - 1 && m.frank[j] == m.r - 1 && m.rank[a & b] == m.r - 2) {
                    int x = hypindex[u], y = hypindex[v];
                    graph.adj[x] |= U(1) << y;
                    graph.adj[y] |= U(1) << x;
                }
            }
        occurrence.resize(2 * variables);
        value.assign(variables, -1);
        for (const auto &c : unique) {
            Clause cl;
            cl.len = c.size();
            copy(c.begin(), c.end(), cl.lit.begin());
            int id = clauses.size();
            clauses.push_back(cl);
            for (int l : c)
                occurrence[2 * (abs(l) - 1) + (l > 0)].push_back(id);
        }
        int top = fvar[m.findex[m.full]];
        if (!assign(top, 1) || !propagate())
            throw runtime_error("top flat inconsistent");
    }
    bool assign(int v, int val) {
        if (value[v] >= 0)
            return value[v] == val;
        value[v] = val;
        trail.push_back(v);
        return true;
    }
    bool propagate() {
        while (head < trail.size()) {
            int v = trail[head++];
            // A negative literal becomes false under 1; a positive one under 0.
            for (int ci : occurrence[2 * v + (value[v] == 0)]) {
                const auto &c = clauses[ci];
                int unknown = 0, last = 0;
                bool satisfied = false;
                for (int j = 0; j < c.len; j++) {
                    int l = c.lit[j], a = value[abs(l) - 1];
                    if (a < 0) {
                        unknown++;
                        last = l;
                    } else if ((a == 1) == (l > 0)) {
                        satisfied = true;
                        break;
                    }
                }
                if (satisfied)
                    continue;
                if (!unknown)
                    return false;
                if (unknown == 1 && !assign(abs(last) - 1, last > 0))
                    return false;
            }
        }
        return true;
    }
    void rollback(size_t size) {
        while (trail.size() > size) {
            value[trail.back()] = -1;
            trail.pop_back();
        }
        head = trail.size();
    }
    U solve() {
        if ((++nodes & 1023) == 0 &&
            chrono::duration<double>(chrono::steady_clock::now() - began).count() > seconds)
            throw runtime_error("timeout");
        int chosen = -1;
        size_t score = 0;
        for (int v = 0; v < variables; v++)
            if (value[v] < 0 && vrank[v] <= mat.r - 2) {
                size_t s = occurrence[2 * v].size() + occurrence[2 * v + 1].size();
                if (chosen < 0 || s > score) {
                    chosen = v;
                    score = s;
                }
            }
        if (chosen >= 0) {
            U answer = 0;
            size_t checkpoint = trail.size();
            for (int val : {1, 0}) {
                if (assign(chosen, val) && propagate())
                    answer += solve();
                rollback(checkpoint);
            }
            return answer;
        }
        U allowed = 0;
        for (size_t i = 0; i < hypvar.size(); i++)
            if (value[hypvar[i]] < 0) {
                if (graph.adj[i] >> i & 1)
                    throw runtime_error("unresolved orbit self-conflict");
                allowed |= U(1) << i;
            }
        leaves++;
        return graph.solve(allowed);
    }
    U count() { return solve(); }
};

int main(int argc, char **argv) {
    if (argc < 2) {
        cerr << "usage: count_extensions all|coloop [seconds_per_class=60] [cache=32768] [paired_coloop=0]\n";
        return 2;
    }
    string mode = argv[1];
    if (mode != "all" && mode != "coloop") return 2;
    double limit = argc > 2 ? stod(argv[2]) : 60;
    size_t cache = argc > 3 ? stoull(argv[3]) : 32768;
    bool paired = argc > 4 && stoi(argv[4]);
    string line;
    uint64_t row = 0;
    while (getline(cin, line)) {
        if (line.empty()) continue;
        auto began = chrono::steady_clock::now();
        try {
            Matroid m(line);
            auto group = m.automorphisms();
            auto classes = conjugacy_classes(group, m.n);
            uint64_t factorial = 1;
            for (int i = 2; i <= m.n; i++) factorial *= i;
            if (group.empty() || factorial % group.size()) throw runtime_error("bad automorphism order");
            if (paired && (mode != "all" || m.n + 1 != 2 * m.r))
                throw runtime_error("paired coloop requires balanced rank");
            map<string, cpp_int> moments;
            for (const auto &cls : classes) {
                U count = mode == "coloop" ? 1 : CutCounter(m, cls.representative, limit, cache).count();
                if (paired) count++;
                moments[cycle_type(cls.representative, m.n)] +=
                    cpp_int(dec(count)) * cls.size * (factorial / group.size());
            }
            cout << "{\"row\":" << row << ",\"status\":\"complete\",\"moments\":{";
            bool comma = false;
            for (const auto &[type, value] : moments) {
                if (comma) cout << ',';
                comma = true;
                cout << '"' << type << "\":\"" << value << '"';
            }
            cout << "},\"seconds\":"
                 << chrono::duration<double>(chrono::steady_clock::now() - began).count()
                 << "}" << endl;
        } catch (const exception &e) {
            cout << "{\"row\":" << row << ",\"status\":\"incomplete\",\"error\":\""
                 << e.what() << "\",\"seconds\":"
                 << chrono::duration<double>(chrono::steady_clock::now() - began).count()
                 << "}" << endl;
        }
        row++;
    }
}
