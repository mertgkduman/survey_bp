# RelayBP gamma tuning on the original LP1054 code

The user confirmed **one80-iteration uniform-gamma stage followed by one60-iteration disordered-gamma stage**. These are maximum leg lengths, with at most140 sweeps per CSS component,280 summed component sweeps per physical shot. Relay-BP-1 stops on the first syndrome-valid candidate. If stage one succeeds, stage two is skipped. Previous32/128 curves and running source jobs are preserved.

The memory equation is Lambda_j(t)=(1-gamma_j)*Lambda_j(0)+gamma_j*M_j(t-1), Relay paper Eq4. The first leg uses the same scalar gamma0 on all variables. The second draws gamma_j independently from a chosen interval, once per variable/shot, and holds it fixed for that leg. Final posterior marginals carry between legs; edge messages reset to the channel prior, as in our already-qualified canonical Relay controller. Gamma is distinct from old-message V2C damping d. The canonical BP message equations and existing search traversal are unchanged.

Primary source: https://arxiv.org/html/2506.01779v2, SectionsII–V and AppendixD. That paper uses80/60 caps and problem-dependent gamma intervals for circuit decoding, often with many additional legs. This is the user's expressly selected **two-leg code-capacity adaptation**, not reproduction of those circuit curves or a301-leg configuration.

Use the same exact [[1054,140]] Example4 code and six depolarizing probabilities .02,.04,.06,.08,.10,.12. Evaluate both X/Z original syndromes and logical residuals. Physical I/X/Y/Z probabilities are1-p,p/3,p/3,p/3; each binary decoder uses the matched2p/3 prior. No OSD is used in the new gamma policies.

Two numerical backgrounds are fixed before gamma tuning: source NMS(d=0,alpha=.625,beta=0), and the parent's training-selected BP damping/scale/offset at each rate. Only immutable parent training locks and their training-summary hashes are read to select those parameters; parent fresh results never enter gamma selection. Numerical backgrounds are distinct experimental arms, not pooled cohorts.

For each background/rate, evaluate11 uniform gamma values(-.5,-.25,0,.125,.25,.35,.5,.625,.75,.875,1) crossed with18 disorder intervals, plus an exact zero-gamma reset control:199 coarse policies. Intervals cover negative/positive centers, several widths and the source windows[-.24,.66],[-.161,.815],[-.254,.985], plus[-.5,1]. The memory-bias cap1e6 remains unchanged and every clip is counted in lineage. A zero-width interval is an exact fixed coefficient, never an epsilon approximation.

Each policy receives1024 common coarse shots. Preserve the top four genuine-disorder policies, the best from each gamma0 band and the zero-memory control, so coarse zero-failure ties do not discard whole memory regimes. Finalists receive up to32768 independent shots or40 failures. Refine first gamma by±.0625 and interval endpoints by±.125 around the best finalist, preserving every finalist as well; evaluate all refinement candidates on another independent cohort of up to131072 shots or60 failures. Select minimum refinement block LER among nonzero-width disorder policies; ties prefer mean total sweeps, warm decoder time and configuration hash. These finite searches do not prove global optimality.

Fresh fourth-seed confirmation compares five prespecified roles: selected full gamma; uniform first phase with zero second gamma; zero first gamma with selected disorder; zero-gamma80/60 reset; continuous BP140. Exact duplicate controls share one fresh cohort and retain all role labels. Each unique policy stops at20 logical failures or100M shots. Noise streams and memory streams have different seeds; stages are disjoint. All tested settings, stage summaries and ledgers are retained, with no confirmation-based winner selection.

One CPU per background/rate worker,12 workers total. Each worker runs tuning/confirmation, then a fresh Python process in the same single-CPU allocation fully audits every retained row and both endpoints of every1024-shot immutable gzip chunk. Larger chunks reduce the tiny-file overhead seen in earlier studies. Checkpoints are exact; at most one uncommitted chunk repeats after interruption. The scheduler warning handler requeues before the four-day allocation deadline without changing manifests or stopping limits. A dependent collector accepts only complete matching audits.

New timing wraps both component solver calls and includes gamma draws, allocations, path-state storage and candidate selection. Sampling, independent evaluation, external posterior/gamma hashing, JSON and ledger writes are outside that timer. These times are not directly comparable to the parent's provenance-instrumented latency. Mean sweeps, directed edges and latency remain separate. Detailed gamma-vector and full posterior/message hashes allow exact phase/lineage replay.

All fresh catalog curves still require compatible exact settings at two distinct physical rates. Singleton settings stay in tables. Specialized saved policies cannot be silently replaced with plain BP by the experiment builder. Existing code choices, custom matrices/Stim, raw evidence, old frozen sources, archivedv1 and GSD phase/model settings are preserved.

Run from the repository:

```
PYTHONPATH=src .venv/bin/python data/reproductions/lp1054-relay-gamma80-60/run.py --freeze
PYTHONPATH=src .venv/bin/python data/reproductions/lp1054-relay-gamma80-60/run.py --submit
PYTHONPATH=src .venv/bin/python data/reproductions/lp1054-relay-gamma80-60/run.py --collect
```
