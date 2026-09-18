// Exact modular-cut moments. The original independent-set kernel is unchanged.
#define main original_split_main
#include "split_count.cpp"
#undef main

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
    bool sparse = true;
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
            int k = __builtin_popcount(unsigned(s));
            if ((k == r - 1 && rank[s] != r - 1) || (k == r + 1 && rank[s] != r))
                sparse = false;
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
    vector<char> bad;
    vector<Clause> clauses;
    vector<vector<int>> occurrence;
    vector<int8_t> value;
    vector<int> trail;
    size_t head = 0;
    Counter graph;
    uint64_t nodes = 0, leaves = 0;
    bool nonsp;
    chrono::steady_clock::time_point began;
    double seconds;

    CutCounter(const Matroid &m, const Perm &p, bool nonsp_, double limit, size_t cache)
        : mat(m), nonsp(nonsp_), seconds(limit) {
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
        bad.assign(variables, false);
        hypindex.assign(variables, -1);
        for (size_t i = 0; i < m.flats.size(); i++) {
            int v = fvar[i];
            if (m.frank[i] <= m.r - 2 ||
                (m.frank[i] == m.r - 1 && __builtin_popcount(unsigned(m.flats[i])) == m.r))
                bad[v] = true;
        }
        for (int v = 0; v < variables; v++)
            if (vrank[v] == m.r - 1) {
                hypindex[v] = hypvar.size();
                hypvar.push_back(v);
            }
        if (hypvar.size() > 126)
            throw runtime_error("hyperplane engine limit");
        graph.adj.resize(hypvar.size());
        graph.memo.reserve(cache);
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
    U solve(bool need_bad) {
        if ((++nodes & 1023) == 0 &&
            chrono::duration<double>(chrono::steady_clock::now() - began).count() > seconds)
            throw runtime_error("timeout");
        if (need_bad)
            for (int v = 0; v < variables; v++)
                if (bad[v] && value[v] == 1) {
                    need_bad = false;
                    break;
                }
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
                    answer += solve(need_bad);
                rollback(checkpoint);
            }
            return answer;
        }
        U allowed = 0, bad_allowed = 0;
        for (size_t i = 0; i < hypvar.size(); i++)
            if (value[hypvar[i]] < 0) {
                if (graph.adj[i] >> i & 1)
                    throw runtime_error("unresolved orbit self-conflict");
                allowed |= U(1) << i;
                if (bad[hypvar[i]])
                    bad_allowed |= U(1) << i;
            }
        leaves++;
        if (!need_bad)
            return graph.solve(allowed);
        // Disjoint first-true branches; never count the all-bad-false family.
        U answer = 0;
        while (bad_allowed) {
            int v = first(bad_allowed);
            bad_allowed &= bad_allowed - 1;
            allowed &= ~(U(1) << v);
            answer += graph.solve(allowed & ~graph.adj[v]);
        }
        return answer;
    }
    U count() {
        return solve(nonsp && mat.sparse);
    }
};

int main(int argc, char **argv) {
    if (argc < 2) {
        cerr << "usage: extension_worker nonsp|all|coloop [seconds_per_class=60] [cache=32768] "
                "[paired_coloop=0]\n";
        return 2;
    }
    string mode = argv[1];
    double limit = argc > 2 ? stod(argv[2]) : 60;
    size_t cache = argc > 3 ? stoull(argv[3]) : 32768;
    bool paired = argc > 4 ? stoi(argv[4]) : false;
    if (mode != "nonsp" && mode != "all" && mode != "coloop" && mode != "inspect")
        return 2;
    string line;
    uint64_t row = 0;
    while (getline(cin, line)) {
        if (line.empty())
            continue;
        auto start = chrono::steady_clock::now();
        try {
            Matroid m(line);
            if (paired && (m.n + 1 != 2 * m.r || mode != "nonsp"))
                throw runtime_error("paired coloop only for balanced nonsp count");
            if (mode == "inspect") {
                int lower = 0, hyp = 0;
                for (int rank : m.frank) {
                    lower += rank <= m.r - 2;
                    hyp += rank == m.r - 1;
                }
                cout << "{\"row\":" << row++
                     << ",\"status\":\"complete\",\"sparse\":" << (m.sparse ? "true" : "false")
                     << ",\"flats\":" << m.flats.size() << ",\"lower\":" << lower
                     << ",\"hyperplanes\":" << hyp << "}" << endl;
                continue;
            }
            auto group = m.automorphisms();
            auto classes = conjugacy_classes(group, m.n);
            uint64_t factorial = 1;
            for (int i = 2; i <= m.n; i++)
                factorial *= i;
            if (!group.size() || factorial % group.size())
                throw runtime_error("invalid group order");
            map<string, cpp_int> moments;
            uint64_t nodes = 0, leaves = 0, calls = 0, hits = 0;
            U identity_count = 0;
            for (const auto &cls : classes) {
                U count = 1;
                if (mode != "coloop") {
                    CutCounter c(m, cls.representative, mode == "nonsp", limit, cache);
                    count = c.count();
                    nodes += c.nodes;
                    leaves += c.leaves;
                    calls += c.graph.calls;
                    hits += c.graph.hits;
                    if (paired)
                        count++;
                }
                string type = cycle_type(cls.representative, m.n);
                bool identity = true;
                for (int i = 0; i < m.n; i++)
                    if (cls.representative[i] != i)
                        identity = false;
                if (identity)
                    identity_count = count;
                moments[type] += cpp_int(dec(count)) * cls.size * (factorial / group.size());
            }
            cout << "{\"row\":" << row << ",\"status\":\"complete\",\"n\":" << m.n
                 << ",\"rank\":" << m.r << ",\"sparse\":" << (m.sparse ? "true" : "false")
                 << ",\"flats\":" << m.flats.size() << ",\"aut\":" << group.size()
                 << ",\"classes\":" << classes.size() << ",\"identity_extensions\":\""
                 << dec(identity_count) << "\",\"nodes\":" << nodes << ",\"leaves\":" << leaves
                 << ",\"graph_calls\":" << calls << ",\"graph_hits\":" << hits << ",\"moments\":{";
            bool comma = false;
            for (auto &[type, v] : moments) {
                if (comma)
                    cout << ',';
                comma = true;
                cout << '"' << type << "\":\"" << v << '"';
            }
            cout << "},\"seconds\":"
                 << chrono::duration<double>(chrono::steady_clock::now() - start).count() << "}"
                 << endl;
        } catch (const exception &e) {
            cout << "{\"row\":" << row << ",\"status\":\"incomplete\",\"error\":\"" << e.what()
                 << "\",\"seconds\":"
                 << chrono::duration<double>(chrono::steady_clock::now() - start).count() << "}"
                 << endl;
        }
        row++;
    }
}
