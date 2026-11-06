---
quick_id: 261106-nd0
reviewed: 2026-11-06
status: passed_with_declared_limitations
simulation_campaigns_launched: false
---

# Scientific review

The implementation resolves the five blocking contracts in `261106-nd0-PLAN-CHECK.md`. This review used source inspection and small deterministic fixtures only; it did not launch a decoding campaign or reinterpret retained measurements.

## Resolved contracts

1. **Rate coordinates:** Pure depolarizing plots retain physical \(p\). A mixed X-only/depolarizing comparison uses \(p_{\mathrm{bit\ flip}}\), transforms only depolarizing coordinates by \(2p_{\mathrm{depolarizing}}/3\), and leaves stored observations unchanged. Explicit, circuit, and unknown channels are not inferred or transformed.
2. **Zero failures:** A zero-failure upper limit remains an observation with its interval/bound, but it breaks the line path. It is not treated as a measured nonzero error rate.
3. **Cohorts:** Exact reused evidence is deduplicated without adding denominators. Statistical pooling requires an explicit `independent_fixed_iid_disjoint_v1` contract, known implementation identity, distinct retained paths and seeds, and fixed-IID binomial counts. Adaptive, importance-weighted, selection/confirmation, or otherwise unproved cohorts remain unpooled. The current public projection contains no duplicate x-coordinate inside a curve and performs no unproved pooling.
4. **Stopping:** Every rate point has at least one positive boundary. Empty fields mean no limit. `any` stops at the first enabled boundary; `all` treats shots as a target and stops only after every enabled boundary is reached. Uniform and complete per-point limits use the same resolver in validation, execution, summary regeneration, and import. Optional stopping suppresses fixed-\(N\) Wilson claims. The old aggregate `max_shots` field is retained only as a nullable legacy hard ceiling.
5. **Circuit outcomes:** Total failures remain observable mismatches. For new detailed ledgers, Type I is an observable failure without detector fit and Type II is an observable failure with detector fit; therefore Type I + Type II equals total observable failures. Detector nonconvergence without an observable mismatch is reported separately. Old ledgers and retained reports that lack the joint partition keep Type I/II as unavailable rather than receiving invented counts.
6. **Circuit sampling and sweeps:** Stim prefixes and retained shots are drawn in identical one-shot chunks, avoiding batch-shape-dependent stream changes. A rate sweep replaces only noisy-gate arguments equal to the declared source probability; each resulting Stim circuit and DEM is recompiled and recorded. Prefix draws and retained shots both count against the legacy ceiling.
7. **Policy composition:** Q-BPGD now delegates each within-round update to the selected canonical Q-BP policy sweep. Fixation updates the working prior, while the committed variable-to-check buffer persists into the next sweep. Damping, check rule, resolution/rounding scope, hard decision, and zero-syndrome policy therefore affect the real recurrence rather than only the UI or manifest. Rounds, fixations, and sweeps are bounded and replay-validated.
8. **Frozen baseline:** With no policy overlay, Q-BPGD still dispatches to the frozen v2 recurrence. A nontrivial fixation fixture also shows that an explicit mathematically equivalent float64 SP policy produces the same candidate, sweep count, round count, fixation count, and convergence result.
9. **Evidence boundaries:** The current circuit CPU-profile report is registered once; the older repeated-output report is provenance only. Its claim remains a local mechanism/throughput profile, not a paper-curve reproduction. The three-qubit fixture is absent from the public v2 registry while internal tests and archived v1 remain intact.

## Verification performed

The focused Python/Node-backed suite passed **82 tests**:

```text
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/research/test_runner.py \
  tests/research/test_stopping_import.py \
  tests/research/test_export.py \
  tests/research/test_plot_coordinates.py \
  tests/research/test_curve_projection.py \
  tests/canonical/quaternary/test_compiled_qbpgd_tuned.py

82 passed in 15.71s
```

The coordinate fixtures cover mixed and pure depolarizing views, explicit/circuit nonconversion, source-data immutability, and zero-bound path breaks. Execution/import fixtures cover negative and nullable budgets, first/all stopping, target-only runs, legacy caps and ledgers, circuit flag replay, circuit prefix identity, Q-BPGD policy composition, and frozen no-policy behavior.

## Declared limitations

- Circuit “Type I/II” is this workbench's explicitly defined flagged/unflagged observable-failure partition, not a claim of universal terminology. User-facing descriptions should retain those words alongside the labels.
- Fixed-\(N\) Wilson intervals are intentionally unavailable for failure-target/adaptive stopping. A sequentially valid interval would require a separately specified estimator.
- Pooling is deliberately opt-in. Repeated cohorts without a machine-verifiable independence contract appear as retained evidence members, not a larger effective sample.
- One-shot Stim sampling is chosen for deterministic prefix/retained-shot identity and may reduce throughput; recorded timing scope must continue to say what is timed.
- Historical stop-failure-only code-capacity ledgers remain importable without the new marker. New stop modes, per-point limits, nullable caps, circuit subtype targets, and circuit noise sweeps require the extended ledger marker.

Within those stated limits, no unresolved scientific blocker remains for this revision.
