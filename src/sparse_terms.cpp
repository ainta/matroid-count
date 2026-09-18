#define main original_split_main
#include "split_count.cpp"
#undef main
int main(int argc, char **argv) {
    try {
        int n = argc > 1 ? stoi(argv[1]) : 10, r = argc > 2 ? stoi(argv[2]) : 5;
        auto blocks = subsets(n, r);
        vector<int> index(1 << n, -1);
        for (int i = 0; i < int(blocks.size()); i++)
            index[blocks[i]] = i;
        vector<int> part;
        cpp_int correction = 0;
        uint64_t fac = 1;
        for (int i = 2; i <= n; i++)
            fac *= i;
        auto evaluate = [&]() {
            if (part.size() == size_t(n))
                return;
            vector<int> perm(n);
            int off = 0;
            map<int, int> mult;
            for (int k : part) {
                mult[k]++;
                for (int j = 0; j < k; j++)
                    perm[off + j] = off + (j + 1) % k;
                off += k;
            }
            uint64_t z = 1;
            for (auto [k, m] : mult) {
                for (int j = 0; j < m; j++)
                    z *= k;
                for (int j = 2; j <= m; j++)
                    z *= j;
            }
            auto image = [&](unsigned s) {
                unsigned t = 0;
                while (s) {
                    int v = __builtin_ctz(s);
                    s &= s - 1;
                    t |= 1u << perm[v];
                }
                return t;
            };
            vector<int> orbit(blocks.size(), -1);
            int no = 0;
            for (int i = 0; i < int(blocks.size()); i++)
                if (orbit[i] < 0) {
                    int j = i;
                    do {
                        orbit[j] = no;
                        j = index[image(blocks[j])];
                    } while (j != i);
                    no++;
                }
            vector<bool> bad(no);
            vector<pair<int, int>> edges;
            for (int i = 0; i < int(blocks.size()); i++)
                for (int j = 0; j < i; j++)
                    if (__builtin_popcount(blocks[i] ^ blocks[j]) == 2) {
                        if (orbit[i] == orbit[j])
                            bad[orbit[i]] = true;
                        else
                            edges.emplace_back(orbit[i], orbit[j]);
                    }
            vector<int> id(no, -1);
            int nv = 0;
            for (int i = 0; i < no; i++)
                if (!bad[i])
                    id[i] = nv++;
            if (nv > 126)
                throw runtime_error("graph capacity");
            Counter c;
            c.memo.reserve(131072);
            c.adj.resize(nv);
            c.limit = 60;
            for (auto [a, b] : edges)
                if (!bad[a] && !bad[b]) {
                    c.adj[id[a]] |= U(1) << id[b];
                    c.adj[id[b]] |= U(1) << id[a];
                }
            c.start = chrono::steady_clock::now();
            U answer = c.solve((U(1) << nv) - 1);
            correction += cpp_int(dec(answer)) * (fac / z);
            cout << "{\"cycle_type\":[";
            for (size_t i = 0; i < part.size(); i++) {
                if (i)
                    cout << ',';
                cout << part[i];
            }
            cout << "],\"fixed\":\"" << dec(answer) << "\",\"centralizer\":" << z << "}" << endl;
        };
        auto generate = [&](auto &&self, int left, int lower) -> void {
            if (!left) {
                evaluate();
                return;
            }
            for (int k = lower; k <= left; k++) {
                part.push_back(k);
                self(self, left - k, k);
                part.pop_back();
            }
        };
        generate(generate, n, 1);
        cerr << correction << '\n';
        return 0;
    } catch (exception &e) {
        cerr << e.what() << '\n';
        return 2;
    }
}
