# Beam/RelayBP finalist refinement across latency budgets

This separate prospective study retains all results from the [first search study](../roffe-2005-07016-search/README.md). Its 512-shot coarse screen often gives many zero-failure ties. Taking only the three fastest tied arms can exclude stronger, slower search settings before the larger finalist sample. This design expands finalist diversity; it changes no numerical kernel or original experiment.

This follow-up was designed after observing initial confirmations and low actual budget use in the first study. Those observations motivated the design change; they are development evidence. Numerical proposals use training files only, and all follow-up selection and evaluation samples use new seeds. The follow-up is not represented as preregistered before the first study's outcomes.

Reuse only the immutable **training** history and selected control specifications from the first campaign. Parent confirmation outcomes are never read for proposal or parameter selection. For each of the same four OSD-0 mean-time budgets (.5,1,2,4), retain the parent fast LER winner, the best two training arms ordered by LER then closeness to that budget, and the best such candidate separately for solution counts1 and4. Proposals admit coarse measured ratios up to1.25 times the target, allowing recalibration drift; all previous selected controls are also retained. Deduplicate exact controls across targets. This intentionally preserves both fast and budget-filling arms when coarse counts tie. It is a finite proposal heuristic, not a global optimum.

Remeasure every proposal on a new finalist seed **2026111562**, at most65,536 shots or100 failures, with a new same-CPU five-by1024-shot canonical BP+OSD-0 reference. Select minimum LER under110% of each latency budget, ties mean iterations/runtime/digest. Unmet budgets stay explicit. Freeze each selection before fresh confirmation with seed **2026111563**,20 logical failures or100 million shots. Different seeds/stages/studies are never pooled. Actual confirmation latency and1%-bin p50/p95/p99 remain explicit. All original109 X-only strata and both methods receive one CPU each.

Every numerical/event/ledger/reference/endpoint audit helper is imported from the unchanged source-pinned first study. Each new worker depends on completion of its corresponding first-study worker (`aftercorr`). The final collector requires both the new array and the original complete full-audit collector to succeed. It checks parent plan/selection hashes, exact regeneration of all training-only proposals and completeness of the parent audit, then independently audits every new finalist and confirmation ledger. Source selection links and old confirmation results remain separate. No parent measurement is rerun. Qualification oracle and browser checks from the unchanged decoder still apply; new proposal/selection/dependency/resume tests cover this orchestration.

```sh
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-search-frontier/run.py --freeze
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-search-frontier/run.py --test-only
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-search-frontier/run.py --submit
```

The first study's controller definitions, complete catalogs, source claims and latency scope apply. This remains a controlled CSS X-only adaptation of BeamSearch/RelayBP, not circuit-paper reproduction or Pauli Q-BP. Runtime/accuracy gains require fresh confirmation; zero-failure training and pilot data are insufficient to claim OSD-level LER.
