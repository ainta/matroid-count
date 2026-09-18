// Exact S_n Burnside correction, NOT quotient by Johnson-graph complementation.
#define main split_program_main
#include "split_count.cpp"
#undef main
int main(int argc, char **argv) {
    try {
        if (argc < 4)
            throw runtime_error(
                "usage: burnside_sparse n r labeled_identity_or_dash [seconds_per_type=60]");
        int n = stoi(argv[1]), r = stoi(argv[2]);
        if (n < 2 || n > 10 || r < 1 || r >= n)
            throw runtime_error("supported: 2<=n<=10, 0<r<n");
        double seconds = argc > 4 ? stod(argv[4]) : 60;
        auto vertices = subsets(n, r);
        int full = (1 << n) - 1;
        vector<int> index(1 << n, -1);
        for (int i = 0; i < (int)vertices.size(); i++)
            index[vertices[i]] = i;
        uint64_t fac = 1;
        for (int i = 2; i <= n; i++)
            fac *= i;
        cpp_int numerator = 0;
        vector<int> part;
        bool complete = true;
        int types = 0;
        uint64_t allcalls = 0;
        auto start = chrono::steady_clock::now();
        auto eval = [&]() {
            if (part.size() == size_t(n))
                return;
            int p[12];
            int off = 0;
            map<int, int> mult;
            for (int k : part) {
                mult[k]++;
                for (int j = 0; j < k; j++)
                    p[off + j] = off + (j + 1) % k;
                off += k;
            }
            uint64_t z = 1;
            for (auto [k, a] : mult) {
                for (int j = 0; j < a; j++)
                    z *= k;
                for (int j = 2; j <= a; j++)
                    z *= j;
            }
            vector<int> orbit(vertices.size(), -1);
            int count = 0;
            auto image = [&](unsigned s) {
                unsigned t = 0;
                while (s) {
                    int j = __builtin_ctz(s);
                    s &= s - 1;
                    t |= 1u << p[j];
                }
                return t;
            };
            for (int i = 0; i < (int)vertices.size(); i++)
                if (orbit[i] < 0) {
                    int j = i;
                    do {
                        orbit[j] = count;
                        j = index[image(vertices[j])];
                    } while (j != i);
                    count++;
                }
            vector<pair<int, int>> edges;
            vector<bool> bad(count);
            for (int i = 0; i < (int)vertices.size(); i++)
                for (int j = i + 1; j < (int)vertices.size(); j++)
                    if (__builtin_popcount(vertices[i] ^ vertices[j]) == 2) {
                        if (orbit[i] == orbit[j])
                            bad[orbit[i]] = true;
                        else
                            edges.push_back({orbit[i], orbit[j]});
                    }
            vector<int> newid(count, -1);
            int valid = 0;
            for (int j = 0; j < count; j++)
                if (!bad[j])
                    newid[j] = valid++;
            if (valid > 128)
                throw runtime_error("quotient exceeds 128-vertex engine");
            Counter c;
            c.limit = seconds;
            c.cap = 131072;
            c.memo.reserve(c.cap);
            c.adj.resize(valid);
            for (auto [a, b] : edges)
                if (!bad[a] && !bad[b]) {
                    c.adj[newid[a]] |= U(1) << newid[b];
                    c.adj[newid[b]] |= U(1) << newid[a];
                }
            U all = valid == 128 ? ~U(0) : (U(1) << valid) - 1;
            c.start = chrono::steady_clock::now();
            types++;
            try {
                U fixed = c.solve(all);
                numerator += cpp_int(dec(fixed)) * (fac / z);
            } catch (runtime_error &) {
                complete = false;
            }
            allcalls += c.calls;
        };
        auto partitions = [&](auto &&self, int left, int lower) -> void {
            if (!left) {
                eval();
                return;
            }
            for (int k = lower; k <= left; k++) {
                part.push_back(k);
                self(self, left - k, k);
                part.pop_back();
            }
        };
        partitions(partitions, n, 1);
        cout << "{\"status\":\"" << (complete ? "complete" : "partial") << "\",\"n\":" << n
             << ",\"r\":" << r << ",\"nonidentity_types\":" << types
             << ",\"nonidentity_numerator\":\"" << numerator << "\",\"calls\":" << allcalls;
        if (string(argv[3]) != "-" && complete) {
            cpp_int identity(argv[3]);
            cpp_int fullsum = numerator + identity;
            if (fullsum % fac != 0)
                throw runtime_error("Burnside numerator is not divisible by n!");
            cout << ",\"labeled\":\"" << identity << "\",\"unlabeled\":\"" << fullsum / fac << "\"";
        }
        cout << ",\"seconds\":"
             << chrono::duration<double>(chrono::steady_clock::now() - start).count() << "}\n";
        return complete ? 0 : 3;
    } catch (exception &e) {
        cerr << e.what() << '\n';
        return 2;
    }
}
