#include <algorithm>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
int main(int argc, char **argv) {
    if (argc != 6)
        return 2;
    int n = stoi(argv[1]), r = stoi(argv[2]), full = (1 << n) - 1;
    if (n < 1 || n > 9 || r < 0 || r > n)
        return 2;
    ifstream in(argv[3]);
    ofstream out(argv[4]), dualout(argv[5]);
    if (!in || !out || !dualout)
        return 2;
    vector<int> masks;
    for (int s = 0; s <= full; ++s)
        if (__builtin_popcount(unsigned(s)) == r)
            masks.push_back(s);
    string line;
    unsigned rows = 0;
    while (getline(in, line)) {
        if (line.size() != masks.size() || line.find('*') == string::npos)
            throw runtime_error("invalid colex");
        vector<int> independent(1 << n), ranks(1 << n);
        for (size_t i = 0; i < line.size(); ++i) {
            if (line[i] != '*' && line[i] != '0')
                throw runtime_error("invalid basis bit");
            independent[masks[i]] = line[i] == '*';
        }
        for (int i = 0; i < n; ++i)
            for (int s = full; s >= 0; --s)
                if (!(s >> i & 1))
                    independent[s] |= independent[s | 1 << i];
        for (int s = 0; s <= full; ++s)
            if (independent[s])
                ranks[s] = __builtin_popcount(unsigned(s));
        for (int i = 0; i < n; ++i)
            for (int s = 0; s <= full; ++s)
                if (s >> i & 1)
                    ranks[s] = max(ranks[s], ranks[s ^ (1 << i)]);
        if (ranks.back() != r)
            throw runtime_error("rank mismatch");
        for (int s = 0; s <= full; ++s)
            out << char('0' + ranks[s]);
        out << '\n';
        for (int s = 0; s <= full; ++s)
            dualout << char('0' + __builtin_popcount(unsigned(s)) + ranks[full ^ s] - r);
        dualout << '\n';
        ++rows;
    }
    if (!out || !dualout)
        return 2;
    cout << rows << '\n';
}
