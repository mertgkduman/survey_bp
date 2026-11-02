# B1/C2 depolarizing follow-up running

Active task: add depolarizing noise for B1/C2 to the completed cross-code study,
using plain binary BP v2 and QBP v2, T=100, p=0.04,...,0.10. Execution is under
`data/reproductions/yao-2312-10950-cross-code/depolarizing/`.

Update: all B1 points and C2 through p=0.08 are complete and independently
audited. Only array tasks 60921740_13 (C2 p=0.09) and _14 (p=0.10) remain
running. All completed main estimates exceed 100 failures. B1 p=0.06 is
2063/23530 binary failures versus 242/23530 QBP; C2 p=0.06 is 3945/20000
versus 568/20000. First ten completed audited final result directories have
already been committed; stage the remaining five only after completion.

Pilot array 60921180 completed all 14 2,000-shot tasks. Every pilot ledger
was independently audited before a fresh fixed follow-up was chosen. The
381,309-shot follow-up is frozen in `campaign.json` with 15 disjoint shards,
running as array 60921740 (one CPU/4 GiB each, maximum parallelism 24,
three-hour wall limits). Plans and pilot evidence are committed. Pilot seeds
use a different namespace from the final cohort and are excluded from final
estimates. New true priors are joint (1-p,p/3,p/3,p/3), binary marginals 2p/3.

Do not modify frozen execution files `study.py`, `run.py`, `decoders.json`,
or any parent files in `implementation_hashes()` while this campaign exists.
Analysis and rendering code can be revised independently. The earlier X-only
experiment remains unchanged.

Unified exec session 23292 runs `PYTHONPATH=src OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1 python .../depolarizing/assess.py --wait`. It audits
each final shard as it completes, then produces all four-code depolarizing
CSVs/plots/report using hash-verified A5/B2 results from the parent study.
Its loaded plotting function predates `sharey='row'`; after completion run
the current `assess.py --render` to rebuild the current report and plots from
hash-verified artifacts. No repeated full audit is necessary unless source
data or execution semantics change.

The dynamically loaded independent syndrome evaluator must use `@njit`
without disk caching: a test-generated `<dynamic>` cache module caused the
first follow-up freezer to fail before creating a plan. It was fixed, then
all pilot ledgers and replays passed. Three focused tests currently pass,
covering correct priors, separate X/Z logical signatures and an independently
indexed syndrome traversal against dense Pauli algebra.

Required before completion: all 15 final tasks finish; the final ledger audit
finishes; review precision labels and plots; archive only completed compressed
final result directories and report artifacts; update README if needed; mark
this task complete and add its row to STATE.md. Do not claim all estimates
reach 100 failures unless the final counts support it. Prospective ceilings
permit low-count estimates or exact zero-failure upper bounds, marked clearly.
