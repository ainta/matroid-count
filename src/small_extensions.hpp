// Order-five completion table for independent sets of J(9,4).
// Derived entirely from a complete S9 orbit catalogue; no precomputed counts.
struct SmallExtensions9 {
    using U = __uint128_t;
    struct Row {
        int k;
        U bits;
        uint64_t aut;
    };
    uint64_t choose[127][6]{};
    std::vector<uint8_t> type[6];
    std::vector<uint64_t> extension[6];
    std::vector<std::vector<int>> seeds[6];
    std::vector<uint64_t> weights[6];
    std::vector<unsigned> sets;
    std::vector<U> adjacency;
    std::vector<int> index;
    uint64_t total = 0;
    SmallExtensions9(const std::string &path) : sets(subsets(9, 4)), index(512, -1) {
        for (int i = 0; i < 126; i++)
            index[sets[i]] = i;
        for (int v = 0; v <= 126; v++) {
            choose[v][0] = 1;
            for (int j = 1; j <= 5; j++)
                choose[v][j] = (v ? choose[v - 1][j - 1] + choose[v - 1][j] : 0);
        }
        std::ifstream f(path);
        if (!f)
            throw std::runtime_error("cannot open complete nine-element catalogue");
        std::vector<Row> rows;
        int k;
        uint64_t hi, lo, aut;
        while (f >> k >> hi >> lo >> aut) {
            if (!aut || 362880 % aut)
                throw std::runtime_error("invalid catalogue automorphism");
            U bits = (U(hi) << 64) | lo;
            if (pc(bits) != k)
                throw std::runtime_error("catalogue cardinality mismatch");
            rows.push_back({k, bits, aut});
            uint64_t w = 362880 / aut;
            total += w;
            if (k <= 5) {
                std::vector<int> s;
                U t = bits;
                while (t) {
                    s.push_back(first(t));
                    t &= t - 1;
                }
                seeds[k].push_back(s);
                weights[k].push_back(w);
            }
        }
        // Completeness is a caller obligation. This guard catches truncated inputs.
        if (rows.size() != 113063 || seeds[0].size() != 1 || seeds[4].size() != 41)
            throw std::runtime_error("need complete J(9,4) orbit catalogue");
        for (int j = 0; j <= 5; j++) {
            type[j].assign(choose[126][j], 0);
            extension[j].assign(seeds[j].size() + 1, 0);
            if (seeds[j].size() > 254)
                throw std::runtime_error("type index overflow");
        }
        type[0][0] = 1;
        std::array<int, 9> p;
        std::iota(p.begin(), p.end(), 0);
        do {
            unsigned map[512];
            map[0] = 0;
            for (unsigned s = 1; s < 512; s++) {
                unsigned b = s & -s;
                map[s] = map[s ^ b] | (1u << p[__builtin_ctz(b)]);
            }
            int images[126];
            for (int i = 0; i < 126; i++)
                images[i] = index[map[sets[i]]];
            for (int j = 1; j <= 5; j++)
                for (size_t a = 0; a < seeds[j].size(); a++) {
                    int v[5];
                    for (int b = 0; b < j; b++)
                        v[b] = images[seeds[j][a][b]];
                    std::sort(v, v + j);
                    uint64_t ix = 0;
                    for (int b = 0; b < j; b++)
                        ix += choose[v[b]][b + 1];
                    uint8_t &t = type[j][ix];
                    if (t && t != a + 1)
                        throw std::runtime_error("duplicate seed orbit");
                    t = a + 1;
                }
        } while (std::next_permutation(p.begin(), p.end()));
        // Verify the orbit sizes obtained by expanding the complete ground-set group.
        for (int j = 1; j <= 5; j++) {
            std::vector<uint64_t> freq(seeds[j].size() + 1);
            for (auto t : type[j])
                freq[t]++;
            for (size_t a = 0; a < seeds[j].size(); a++)
                if (freq[a + 1] != weights[j][a])
                    throw std::runtime_error("orbit size check failed");
        }
        for (const auto &row : rows) {
            uint64_t w = 362880 / row.aut;
            int v[126], len = 0;
            U s = row.bits;
            while (s) {
                v[len++] = first(s);
                s &= s - 1;
            }
            auto rec = [&](auto &&self, int at, int depth, uint64_t ix) -> void {
                for (int a = at; a < len; a++) {
                    auto next = ix + choose[v[a]][depth + 1];
                    uint8_t t = type[depth + 1][next];
                    if (!t)
                        throw std::runtime_error("invalid stable subfamily");
                    extension[depth + 1][t] += w;
                    if (depth + 1 < 5)
                        self(self, a + 1, depth + 1, next);
                }
            };
            rec(rec, 0, 0, 0);
        }
        extension[0][1] = total;
        for (int j = 1; j <= 5; j++)
            for (size_t a = 0; a < seeds[j].size(); a++) {
                auto &e = extension[j][a + 1];
                if (e % weights[j][a])
                    throw std::runtime_error("incidence quotient not integral");
                e /= weights[j][a];
            }
        adjacency.resize(126);
        for (int i = 0; i < 126; i++)
            for (int j = 0; j < 126; j++)
                if (__builtin_popcount(sets[i] ^ sets[j]) == 2)
                    adjacency[i] |= U(1) << j;
    }
    uint64_t avoiding(U forbidden) const {
        __int128 ans = total;
        auto rec = [&](auto &&self, U allowed, int depth, uint64_t ix) -> void {
            while (allowed) {
                int v = first(allowed);
                allowed &= allowed - 1;
                if (depth >= 5)
                    throw std::runtime_error("low-order inclusion-exclusion exceeded order five");
                uint64_t next = ix + choose[v][depth + 1];
                auto t = type[depth + 1][next];
                if (!t)
                    throw std::runtime_error("non-independent lookup");
                auto value = extension[depth + 1][t];
                if (depth % 2 == 0)
                    ans -= value;
                else
                    ans += value;
                self(self, allowed & ~adjacency[v], depth + 1, next);
            }
        };
        rec(rec, forbidden, 0, 0);
        if (ans < 0 || ans > total)
            throw std::runtime_error("inclusion-exclusion out of bounds");
        return uint64_t(ans);
    }
};
