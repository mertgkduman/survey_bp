---
quick_id: 261106-nd0
status: issues_found
checked: 2026-11-06
blockers: 5
warnings: 3
---

# Plan check: result semantics and composable builder

The quick-plan scope matches the requested product revision, but five scientific contracts must be made executable before the slice can be considered complete. The present prose plan does not bind those choices, and the current implementation actively contradicts two of them: Q-BPGD rejects policy overlays, and circuit outcomes do not define Type I/II counts.

## Blocking properties

1. **Mixed-channel plots must have one mathematically defined abscissa.**
   - Required property: A pure depolarizing comparison uses physical `p_depolarizing`, with `P(X)=P(Y)=P(Z)=p_depolarizing/3`. A chart that directly compares an X-only binary-BP curve with a depolarizing Q-BP curve uses `p_bit flip`; only the depolarizing coordinates are transformed by `p_bit flip = 2 p_depolarizing / 3`. Selection must use channel metadata, not decoder family or display name. Tables/details must retain both source physical probability and displayed coordinate.
   - Evidence: `app.js` currently derives one generic axis from `x_semantics`; `decoder-display.js` exposes `q=2p/3` in decoder names. The plan says only “explicit physical/marginal rate axes,” which does not specify the conditional transform.

2. **Circuit Type I/II counters must be independently evaluable and must not silently redefine existing observable-failure results.**
   - Required property: The result schema states exactly what Type I, Type II, total failures, detector fit, and observable failure mean for a circuit shot; the event ledger contains enough facts to replay every counter; stopping uses those replayed counters. If Type I is detector-inconsistent output and Type II is detector-consistent observable failure, the product must state whether `failures` is their union or whether Type I/II are independent diagnostics. Existing reports whose `canonical_observable_errors` count only observable mismatches retain that meaning and identity.
   - Evidence: `_circuit_rows` currently records `detector_fit` and `observable_failure`, increments only observable failures, passes zeros for Type I/II stopping, and summaries set Type I/II to null. The retained circuit reports likewise report observable errors and convergence separately.

3. **Every stopping mode must have an unambiguous monotone condition.**
   - Required property: For each rate point, define “first” as stopping when any populated threshold is reached and “all” as stopping when all populated thresholds are reached. The contract must say whether a populated shots field is a target participating in `all` or a hard safety cap that can never be exceeded; it cannot be both. Empty fields are unbounded, all empty is rejected, old v1 `shots` behavior remains stable, and target-only execution is represented honestly rather than receiving a hidden cap. Summary/import replay must use the same condition.
   - Evidence: the current global `sampling.shots` is mandatory and is a hard loop/cap; `_stopping_reason` implements only first-reached; `budgets.max_shots` is an aggregate experiment cap. The plan requests first/all and unlimited fields without resolving the contradiction.

4. **Curve consolidation must prove cohort disjointness or duplicate identity before changing counts.**
   - Required property: Exact reused evidence is shown once without adding its counts. Pooling is allowed only for disjoint, fixed-shot IID binomial cohorts with identical code semantic identity, channel and rate, decoder prior, complete decoder/evaluator identity, and stopping/budget semantics. Pool by event/sample identity (including shot ranges), recompute the declared interval at the declared confidence, and retain all seeds and source assets. Never pool pilot with confirmation, screening/tuning with held-out validation, adaptive stopping, importance-weighted estimates, or overlapping/reused controls without an estimator-specific method.
   - Evidence: current display disambiguates label collisions using `N` and arbitrary `set`; catalog comments already prohibit pooling the Q-BPGD pilot and confirmation. The plan’s “provenance-safe consolidation” does not define a key, overlap proof, or estimator exclusions.

5. **Guided decimation must compose with actual selected BP policies in the kernel recurrence.**
   - Required property: Selecting damping, scaling/resolution, and guided decimation produces one validated policy composition whose within-round sweeps use those selected coefficients and numerical operations while preserving the Q-BPGD persistent-message and fixation lifecycle. Effective settings and work are recorded. Unsupported policy combinations remain visible validation errors; controls are never accepted and ignored.
   - Evidence: `validate_experiment` currently requires Q-BPGD `policy=null`; `CompiledBp4Graph.run_qbpgd` rejects `self.policy` and calls `_decode_qbpgd_v2`, whose sweep has only the frozen float64 v2 cap/product-epsilon/damping parameters. The plan says “composable supported policies” but does not explicitly require this kernel change or a recurrence-level test.

## Warnings

1. **Circuit reports are real bounded local measurements, not missing because of the retired code-capacity clipping profile.** The active author-v0.2.2 report uses min-sum, tie-break one, `T=8`, and reports observable errors, convergence, work, and timing. The older report repeats the same sampled outputs under the previous native package comparison. Register one current measured series and link the older report as provenance; do not pool or double-count them. Preserve the report’s stated claim limit: CPU mechanism/throughput profile, not a paper-curve reproduction.

2. **The public three-qubit removal boundary needs a test.** Remove it from v2 catalog records, selectors, policy family listings, generated contract aliases/defaults, and public example downloads. Existing internal algebra/test fixtures and the immutable v1 archive may remain if they are clearly outside the public v2 product; otherwise “entirely” is unverifiable and can break unrelated scientific tests.

3. **Baseline descriptions and matrix previews need concrete acceptance.** The builder must provide searchable baseline BP and Q-BP specifications; its explanatory panel must render the actual default check/variable updates, damping convention, hard decision, numerical profile/clipping, schedule, and stopping rule. Selecting a registered code must display the materialized `H_X` and `H_Z` for that exact artifact/constructor and update on every code change. A constructor receipt is not itself a parity-check preview.

## Required verification matrix

| Workflow | Passing evidence |
|---|---|
| Q-BP naming/search | No active v2 label says BP4; comma-separated parameter names support prefix keyboard selection in Results and Builder; machine IDs/provenance remain unchanged. |
| Zero failures | A zero-failure point is drawn as an upper-limit/error-bar observation, is excluded from every connecting path segment, and remains `≤ bound` in the table. |
| Rate axes | Pure depolarizing and mixed X-only/depolarizing browser fixtures verify the two axis modes, equation, transformed positions, and original physical values in details/CSV. |
| Consolidation | Duplicate, disjoint-poolable, overlapping, pilot/confirmation, adaptive, and importance-weighted fixtures each take the required path and preserve provenance. |
| Policy composition | A recurrence-level test shows that changing damping/resolution changes Q-BPGD within-round messages/results under the same syndrome; exported effective configuration records both intervention and policies. |
| Code matrices | Selecting two registered codes changes the displayed `H_X/H_Z`; custom validation rejects invalid dimensions/commutation. |
| Circuit sweep | Only Stim noisy-gate probability arguments tied to the declared source rate change; coordinates, repeat counts, observable indices, rec targets, and unrelated probabilities remain unchanged. Every emitted circuit reparses and has an identity/checksum. |
| Sampling | Uniform and per-rate settings, first/all modes, each single threshold, multiple thresholds, all-empty rejection, target-only execution, old-spec replay, summaries, imports, and package round-trip agree. |
| Circuit outcomes | Tiny deterministic fixtures cover detector-inconsistent/consistent and observable-correct/incorrect combinations; ledger replay reproduces Type I/II and stop reasons. |
| Retained circuits | Current report points appear with exact shots/errors/work/time and claim limit; duplicate native-comparison report is not a second curve. |

## Plan-format advisory

The file follows the repository’s established lightweight quick-task style, but `verify.plan-structure` reports no structured tasks, `must_haves`, file list, or runnable checks. Treat the matrix above as the binding completion contract and record the exact commands/results in the quick summary and verification artifacts.
