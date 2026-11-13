# Roffe 2020 regular BP and canonical Q-BP

Primary paper: Roffe, White, Burton and Campbell, *Decoding Across the Quantum
LDPC Code Landscape*, arXiv:2005.07016v2; Phys. Rev. Research 2, 043423 (2020).
This early BP+OSD study credits the original 2019 Panteleev–Kalachev BP-OSD
proposal. Figure 3 directly compares plain BP against BP+OSD-CS.

Reproduce the four **regular BP** curves: toric [[162,2,9]], [[242,2,11]],
[[338,2,13]], [[450,2,15]]. The paper constructs them as symmetric hypergraph
products of ring repetition codes. Our explicit Eq. (4) construction keeps all
redundant checks and uses project row-major ordering and a paired logical basis.
The graph and logical algebra are independently validated. Original ordered
author artifacts are not available; this remains a canonical adaptation.

Use the existing canonical min-sum check and variable updates, flooding,
float64, no damping, matched prior, and alpha_t=1-2^(-t), starting at t=1.
The controller dispatches canonical public sweeps and stops at the first valid
syndrome, or exactly n iterations as specified in Section V. It implements no
message equation itself. The initial zero syndrome still executes one source
iteration. No OSD is invoked. Exact author numerical conventions are unresolved.

Rates come from the original vector Figure 3 in the pinned arXiv source archive.
The four dashed curves contain 25/28/28/28 measured vertices, confirmed against
vertical error bars, with irregular spacing near .10. Reproduce each code's own
grid, rather than filling absent rates or reusing the MacKay interval. The 109
binary points use source X-only noise; the additional 109 Q-BP points use joint
min-sum with the same alpha_t and n-iteration ceiling, and depolarizing p=1.5*p_X.
That matches marginal X/Z rates, not the full source noise model. Q-BP uses the
canonical joint-Pauli MAP decision. Source comparisons apply only to binary BP.

Each point retains 20 quantum block failures (nonconvergence or either nontrivial
logical residual) or 100,000,000 shots, seed 2026111311. Full event ledgers,
independent original-code outcomes, stopping-aware 95% intervals, first/last
replay, exact hashes, mean actual iterations and mean both-directed-edge updates
are retained. Averaging is per retained shot; no discarded speculative work is
counted as retained-shot work. Source ordinates are approximate vector values;
raw author sample counts and intervals are unavailable. Do not claim reproduction
from dispatch, small pilots or unassessed partial results.

The damping confirmation's successful audit submits this study automatically.
At most 16 one-CPU jobs run simultaneously. Do not submit it separately while
that pipeline is still active. Manual recovery commands (PYTHONPATH=src, OMP/BLAS=1):

```
.venv/bin/python data/reproductions/roffe-2005-07016-bp/prepare.py /path/to/pinned-source.tar
.venv/bin/python data/reproductions/roffe-2005-07016-bp/run.py --freeze
.venv/bin/python data/reproductions/roffe-2005-07016-bp/run.py --test-only
.venv/bin/python data/reproductions/roffe-2005-07016-bp/run.py --submit
.venv/bin/python data/reproductions/roffe-2005-07016-bp/run.py --collect
```

The final dependent collector requires all 218 terminal points, audits them,
and refreshes the shared catalog. Failed/missing evidence prevents completion.
Raw ledgers remain local, portable verified summaries are tracked, and all
previous studies and canonical kernels remain unchanged.
