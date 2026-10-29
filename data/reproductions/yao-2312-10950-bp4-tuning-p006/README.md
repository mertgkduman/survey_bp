# BP4 tuning at physical p = 0.06 on Yao A5 and B2

This study tunes the compiled canonical four-Pauli BP kernel on the frozen
[`A5` and `B2` codes](../yao-2312-10950-vanilla/README.md). It reuses the
code receipts, independent syndrome and logical evaluator, and depolarizing
sampler from that study. It is a **canonical tuning study**, not a claim to
recover the unpublished parameter choices in Yao et al. The physical error
rate is always `p=0.06`; the decoder prior `p0` may differ.

The outcome is a block failure: a syndrome mismatch (Type I) or a
syndrome-consistent nonstabilizer residual (Type II). Exact and
stabilizer-equivalent corrections both count as successes. Decoder kernels
receive the syndrome and prior only; the sampled error goes to an independent
outcome evaluator. Each shot has an event ledger row and a hash of the sampled
physical error. Candidates within each code and stage decode exactly the
same error sequence.

**Selected at physical `p=0.06`:** A5 uses float64 v2 SPA with `p0=0.005`,
outgoing V2C damping `d=0.2`, and `T=10,000`; B2 uses `p0=0.15`, `d=0.1`,
and `T=5,000`. The counts, exact 90% intervals, finite-neighborhood decision,
and limitations are in the [final report](results/REPORT.md).
The [paired fairness follow-up](fairness_t100/REPORT.md) compares these
settings with untuned BP4 at equal `T=100` and at approximately equal mean
iterations. Use that follow-up for tuned-versus-untuned effect claims; the
selected long-cap rates alone do not control decoding work.

## Search design

1. An exploratory pilot stops the undamped float64 v2 baseline after **six**
   block failures on each code. The paired screen runs 47 candidate policies
   on those prefixes: A5 `N=1,148`, B2 `N=1,460`. Because `N` depends on
   observed failures, those counts are for ranking only, not rate estimation.
   See [`screen_plan.json`](screen_plan.json) and
   [`results/screen_report.md`](results/screen_report.md).
2. A fresh, fixed-shot refinement compares 26 A5 settings on 12,000 errors
   and 24 B2 settings on 15,000 errors. The 50 runs share a seed within code,
   and all passed the hash/count/stream audit. See
   [`refine_plan.json`](refine_plan.json),
   [`results/refine_report.md`](results/refine_report.md), and the
   [interval plot](results/refine_intervals.png).
3. Before the next seed, the leading settings and neighboring damping, prior,
   iteration-cap, and numerical-policy settings were frozen in
   [`validate_plan.json`](validate_plan.json). Each of 10 settings per code
   receives 50,000 fixed paired errors. The A5 incumbent is float64 v2 SPA,
   `d=0.1, p0=0.06, T=1000`; the B2 incumbent is float64 v2 SPA,
   `d=0.1, p0=0.15, T=100`.
4. The first holdout did **not** meet its prespecified stopping rule: longer
   caps made further paired rescues. Independent follow-up and cap-tail plans
   retain the resulting evidence under `results/extend/`,
   `results/followup/`, `results/tail_a5/`, and `results/tail_b2/`.
   Subsequent fresh-seed plans check prior and damping interactions:
   [`sweet_b2_plan.json`](sweet_b2_plan.json),
   [`joint_final_plan.json`](joint_final_plan.json),
   [`a5_prior_plan.json`](a5_prior_plan.json),
   [`a5_low_prior_plan.json`](a5_low_prior_plan.json),
   [`a5_tiny_prior_plan.json`](a5_tiny_prior_plan.json), and
   [`b2_prior_confirm_plan.json`](b2_prior_confirm_plan.json). A final
   A5 damping/cap neighborhood is frozen in
   [`a5_final_neighborhood_plan.json`](a5_final_neighborhood_plan.json).
   That stage found an improvement at `d=0.2`, so the subsequent local
   prior/damping/cap search is frozen in
   [`a5_d02_neighborhood_plan.json`](a5_d02_neighborhood_plan.json). Their
   candidate registries and audited stage results are retained independently.
5. For cap-only increases, use the exact one-sided 90% upper bound on the
   additional rescue rate. A cap is practically saturated within the tested
   range when this upper bound is smaller than the incumbent's observed LER
   minus its exact two-sided 90% lower limit, and the larger-cap point rate
   remains in that interval. This clarification was recorded in the
   [GSD plan](../../../.planning/quick/261028-kvb-tune-vanilla-bp4-at-p-0-06-on-yao-a5-and/261028-kvb-PLAN.md)
   before the cap-tail runs finished. Paired McNemar p-values remain in the
   tables. This is a finite-neighborhood rule, not proof of equal true rates
   or a global optimum. The final selection and limitations are in
   [`results/REPORT.md`](results/REPORT.md).

All fixed-shot tables retain Type I and Type II counts, mean iterations,
runtime, paired rescue/loss counts, and the exact 90% interval. Runtime is
per decode on the allocated CPU; its absolute value depends on the node.
Results are separated by stage so tuning cannot silently reuse one error
stream as independent validation.

## Decoder files

[`decoders/screen_candidates.json`](decoders/screen_candidates.json),
[`decoders/refine_candidates.json`](decoders/refine_candidates.json), and
[`decoders/validate_candidates.json`](decoders/validate_candidates.json) are
immutable, data-only candidate registries hashed by the corresponding plans.
Later stage registries use the same schema and appear alongside them in
`decoders/`.
Each candidate specifies `kernel`, `p0`, and `max_iterations`:

- `profile_v2` binds the compiled canonical float64 v2 sum-product profile,
  with an explicit outgoing-variable-message damping coefficient, check cap,
  and check-product epsilon. Damping uses
  `m_new = d*m_old + (1-d)*m_proposed`.
- `policy_flooding` binds a composable `BpFloodingPolicy` from its validated
  JSON `policy` spec, including check rule and message resolution. Q8
  `scalar_edges` rounds commute/anticommute edge messages; `all_messages`
  rounds the variable messages too. See the
  [numerical-profile guide](../../../docs/numerical-profiles.md).

These are study-specific decoder files consumed by [`runner.py`](runner.py),
not the general `bp-registry --decoder` format. The selected per-code files
are [`decoders/a5_tuned.json`](decoders/a5_tuned.json) and
[`decoders/b2_tuned.json`](decoders/b2_tuned.json). To try a new setting,
copy this study under a new identity and make a new frozen plan; the runners
refuse to overwrite evidence and check registry and source hashes.

## Replaying and auditing

From the repository root, in the project's qualified Python environment:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/run_task.py --index 0
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_screen.py
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/run_fixed_task.py --plan data/reproductions/yao-2312-10950-bp4-tuning-p006/refine_plan.json --index 0
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py refine
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py validate
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py tail_a5
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py tail_b2
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py sweet_b2
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py a5_tiny_prior
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py a5_final_neighborhood
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py a5_d02_neighborhood
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py b2_prior_confirm
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/compare_tail.py tail_a5
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/compare_tail.py tail_b2
```

Each command that runs a shot requires a new output directory. For a full
replay, copy the study with a new identity before rebuilding plans. On this
HPC cluster, `submit_screen.sh` and `submit_fixed.sh refine|validate` submit
the frozen task arrays. The latter uses node-local Numba caches to avoid a
transient shared-filesystem cache error observed in one refinement task; that
task was rerun unchanged and passed the full ledger audit.

The event ledgers stay on the HPC filesystem and are excluded from Git due to
size. Tracked manifests and summaries contain SHA-256 digests; the analysis
scripts verify every ledger and reconstruct the paired physical sample stream
before reporting results. A checkout without the ledgers can inspect the
frozen policy/summary files but cannot rerun that full audit without first
reproducing the shots.
