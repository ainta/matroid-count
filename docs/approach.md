# Counting method

The program counts matroids on ten elements without constructing ten-element
representatives. It uses one extension counter for every parent matroid.
It counts each rank separately and combines the ranks by duality.

## 1. Generate the nine-element parents

The pinned [IC generator](../vendor/matroid-generator/src/IC.cpp) starts from
the empty matroid and produces one representative of each isomorphism class
through nine elements. We generate ranks up to the midpoint and use duality
for the other ranks. A [converter](../src/colex_to_rank.cpp) computes the rank
of every subset from the generator's basis encoding.

There are 190,214 parents of rank five on nine elements. The complete
nine-element catalogue contains 383,172 classes. The counting program does
not read a downloaded catalogue.

## 2. Count extensions with modular cuts

Let $N$ be a matroid of rank $r$ on nine elements. For each flat $F$ of $N$,
let $x_F$ state whether the new element $e$ lies in the closure of $F$.
The selected flats form a modular cut exactly when

$$
x_F\Rightarrow x_G\quad(F\subseteq G),
\qquad
x_F\land x_G\Rightarrow x_{F\cap G}
\quad\text{if}\quad
r(F)+r(G)=r(F\cup G)+r(F\cap G).
$$

By [Crapo's extension theorem](https://nvlpubs.nist.gov/nistpubs/jres/69B/jresv69Bn1-2p55_A1b.pdf),
nonempty modular cuts correspond bijectively to extensions of rank $r$.
The empty cut adds a coloop and raises the rank
by one. The extension is determined by

$$
r_M(X)=r_N(X),\qquad
r_M(X\cup\{e\})=r_N(X)+1-x_{\operatorname{cl}_N(X)}.
$$

The [C++ worker](../src/count_extensions.cpp) counts cuts invariant under
a specified automorphism $g$ of $N$. It first identifies flats in each
$g$-orbit. It propagates the modular-cut constraints after every assignment.

The worker branches only on orbits of flats of rank at most $r-2$. Once those
variables are fixed, the remaining variables represent hyperplanes.
Distinct hyperplanes $H,K$ form a modular pair exactly when
$r(H\cap K)=r-2$. If both remain undecided, their intersection is false.
Thus they cannot both be selected. An undecided hyperplane orbit is a vertex
of a graph; two orbits are adjacent if any pair of their hyperplanes conflicts.
An orbit with an internal conflict is forced false. The remaining choices
are exactly the independent sets of this graph.

The graph counter uses

$$
i(G)=i(G-v)+i(G-N_G[v]),\qquad i(\varnothing)=1,
$$

where $N_G[v]$ is the closed neighborhood of $v$. It also splits connected
components and caches repeated induced subgraphs. Each graph has its own
cache: a vertex mask does not identify a graph across different parents.
A rank-five parent on nine elements has at most 126 hyperplanes and
130 flats of rank at most three.

## 3. Recover isomorphism classes

Counting extensions up to parent automorphisms counts matroids with a
distinguished element. The number of element orbits varies by matroid.
We therefore use Burnside's lemma on the ten ground-set labels.

Let $F_{10,r}(\lambda)$ be the number of labeled matroids of rank $r$ fixed
by a permutation of cycle type $\lambda$. Write
$z_\lambda=\prod_j j^{a_j}a_j!$, where $a_j$ counts the $j$-cycles.
Then

$$
u_{10,r}=\sum_{\lambda\vdash 10}\frac{F_{10,r}(\lambda)}{z_\lambda}.
$$

There are 42 cycle types. For the 30 types with a fixed point $e$, delete
$e$. If it is not a coloop, the result is a rank-$r$ parent $N$, and the
restricted permutation is an automorphism $g$ of $N$. Fixed extensions
correspond exactly to $g$-invariant nonempty modular cuts. If $e$ is a
coloop, its parent has rank $r-1$ and gives one extension.

The program groups automorphisms by conjugacy class inside each parent's
automorphism group. It multiplies each invariant-cut count by the class
size and the number of labeled copies of the parent. At rank five,
duality pairs the rank-four coloop parents with rank-five parents.
For each cycle type, the program checks that the resulting fixed count
is an integer.

Here is the exact weighting. Let $c(N,g)$ count the nonempty modular cuts
of $N$ preserved by $g$, and let $mathcal M_{9,j}$ contain one parent of
each rank-$j$ isomorphism class. For a cycle type $mu$ on nine elements,

$$
T_{r,mu}=
sum_{Ninmathcal M_{9,r}}rac{9!}{|operatorname{Aut}(N)|}
  sum_{substack{ginoperatorname{Aut}(N)\operatorname{type}(g)=mu}}c(N,g)
+sum_{Ninmathcal M_{9,r-1}}rac{9!}{|operatorname{Aut}(N)|}
  #{ginoperatorname{Aut}(N):operatorname{type}(g)=mu}.
$$

There are $9!/z_mu$ permutations of type $mu$. Each has the same fixed
count, so $F_{10,r}(mucup(1))=z_mu T_{r,mu}/9!$.

For the other 12 cycle types, choose a permutation $\sigma$ of each type.
Make one Boolean variable per orbit of $r$-subsets under $\sigma$.
A true variable selects every subset in its orbit as a basis.
Require at least one basis and impose every basis-exchange clause.
The satisfying assignments are exactly the $\sigma$-fixed matroids of
rank $r$. The [driver](../scripts/count.py) asks Ganak for their exact
number. The largest instance is split into 256 disjoint assignments.

The two procedures give every fixed count in Burnside's sum. Ranks zero
through two use elementary formulas. Duality supplies ranks six through
ten from ranks four through zero.

## Why the count is exact

Every rank-preserving extension appears once as a modular cut of its
deletion parent. Propagation removes assignments that violate the
definition of a modular cut. After each completed assignment to flats
of rank at most $r-2$, the graph counter counts every valid hyperplane
choice once.

The basis-exchange formula describes precisely the matroids fixed by a
permutation with no fixed point. The two sets of permutation types are
disjoint and cover all 42 types. Burnside's lemma then counts each
isomorphism class once.
