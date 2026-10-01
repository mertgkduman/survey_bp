---
phase: 05-guided-and-perturbative-bp-interventions
reviewed: 2026-10-01T02:30:31Z
depth: deep
files_reviewed: 33
files_reviewed_list:
  - README.md
  - data/manifests/phase5-b1-calibration.json
  - data/manifests/phase5-b1-mechanism-pilot.json
  - docs/evidence/phase5-b1-cap-freeze.json
  - docs/evidence/phase5-compute-entitlement.json
  - docs/evidence/phase5-source-decisions.json
  - docs/phase5-interventions.md
  - notebooks/phase5_intervention_analysis.py
  - scripts/execute_phase5_notebook.py
  - scripts/phase5_notebook_support.py
  - scripts/preview_phase5_notebook.py
  - scripts/run_phase5_pilot.py
  - src/bp_registry/canonical/budgets.py
  - src/bp_registry/canonical/contracts.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/guided_decimation.py
  - src/bp_registry/canonical/impulse.py
  - src/bp_registry/canonical/intervention_session.py
  - src/bp_registry/canonical/interventions.py
  - src/bp_registry/canonical/kernel.py
  - src/bp_registry/canonical/phase5.py
  - src/bp_registry/canonical/problems.py
  - src/bp_registry/canonical/restarting.py
  - src/bp_registry/canonical/transformations.py
  - src/bp_registry/canonical/verification.py
  - src/bp_registry/cli.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/phase5_analysis.py
  - src/bp_registry/runner.py
  - tests/canonical/test_budgets.py
  - tests/canonical/test_impulse.py
  - tests/test_phase5_public_execution.py
findings:
  critical: 2
  warning: 4
  info: 0
  total: 6
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-10-01T02:30:31Z
**Depth:** deep
**Files Reviewed:** 33
**Status:** issues_found

## Summary

The Phase 5 public execution path keeps hidden truth outside the controllers and the notebook/evidence loaders constrain their declared project paths. The review found two release-blocking gaps in the promised resource and provenance boundary. In particular, the sealed 300-second per-shot limit is not enforced during controller execution, and several controllers perform budgeted selection or transformation work before reserving the corresponding leaf. The verifier's relative-output spelling regression in `cli.py` is correctly handled for the same working directory used by the public CLI test.

## Narrative Findings (AI reviewer)

The findings below are based on direct call-chain review from the public runner through `_run_phase5_structural_shot`, `execute_phase5_controller`, all six controller families, and the structural ledger verifier. No CPU-heavy test was run because a public replay is active.

## Critical Issues

### CR-01 [BLOCKER]: The declared 300-second shot cap is only checked after all controller work has completed

**File:** `src/bp_registry/canonical/execution.py:929-937`

**Issue:** The Phase 5 path starts a monotonic timer, calls `execute_phase5_controller`, then raises if the elapsed time exceeds the cap. No controller receives a `WallClockLimit` or deadline callback. Consequently a slow controller can run arbitrarily beyond the sealed 300 seconds; the raised exception occurs before the writer is opened at `execution.py:967-969`, so the spent work has neither a terminal record nor replayable deadline evidence. Count limits cannot repair this: they do not bound elapsed wall time and several preprocessing operations are outside reservation (CR-02). This contradicts the manifest cap (`data/manifests/phase5-b1-mechanism-pilot.json:1264-1268`) and the Phase 5 DoS mitigation.

**Fix:** Reuse the existing `WallClockLimit` (`src/bp_registry/canonical/budgets.py:539-570`) as a cooperative deadline. Construct one shared limit from `phase5_max_runtime_seconds` before controller dispatch and start it with `attempt_start`. Thread it as an optional argument through `execute_phase5_controller`, all Phase 5 controllers, and `BpSession.advance`; at declared boundaries, return the existing typed `SessionTransition(False, state, "wall_clock_deadline", None)` before reserving or starting a new leaf. Have the controllers preserve that termination in their existing partial result, which `_project` can already convert to `Phase5Outcome` without a new terminal model.

Acquire `CanonicalEventWriter` and emit `shot_begin` before calling the controller, then append a `runtime` fact containing the typed `BudgetTermination` fields and a normal `termination` event with `wall_clock_deadline`. Update structural verification to require and replay that fact. Check only between atomic leaves: a committed sweep/action/transform stays committed; no new action, target selection, RNG draw, or evaluator call begins after a deadline. Controller-specific traps are (1) preserve the specific termination rather than converting every denied transition to `count_budget_exhausted`; (2) the sign-flip pending target may be retained only as an unselected diagnostic state; (3) branch and restart rows need a coherent terminal row when the deadline arrives between leaves; and (4) no post-deadline release or fresh reset may be started. This is a bounded interface extension, not a new result schema: `Phase5Outcome` already carries `termination`, partial rows, leaves, work, and an optional candidate.

### CR-02 [BLOCKER]: Controllers perform charged target/order/transform work before a work leaf is reserved

**File:** `src/bp_registry/canonical/guided_decimation.py:100-108`; `src/bp_registry/canonical/interventions.py:190-212`, `src/bp_registry/canonical/interventions.py:421-442`, `src/bp_registry/canonical/interventions.py:615-630`; `src/bp_registry/canonical/restarting.py:223-235`, `src/bp_registry/canonical/restarting.py:319-325`

**Issue:** The public ledger represents `WorkVector` leaves as actual committed work, but multiple controllers calculate selection state before the leaf that charges that calculation. Guided decimation computes the reliability maximum and target before `commit_intervention` reserves `ranking_scans`; freezing constructs frustrated-check choices and consumes its deterministic RNG before `IdempotentActionGate.commit`; syndrome flip sorts the full ranking before it reserves `order_generation` and `ranking_scans`; sign flip computes mismatch scores and chooses its target before `stage_posterior_sign`; restart sorts root LLRs before `_reserve_compute`, and constructs the inserted-error vector plus residual syndrome before the transformation reservation. A depleted budget can therefore still cause unrecorded computation and random-stream consumption, while the resulting work receipt and replay falsely present the leaf totals as complete.

**Fix:** Reserve a leaf before each such computation and calculate it only inside the reservation's transactional compute block. For example, reserve `WorkVector(order_generation=1, ranking_scans=n)` before guided/syndrome/restart ordering and before freezing's neighbor permutations; reserve the residual construction and `_views` together before creating `error` or `residual_syndrome`. If admission fails, emit a terminal/attempt row with no derived target and consume no decoder stream. Apply the same pre-leaf boundary to the cooperative wall-clock check in CR-01.

## Warnings

### WR-01 [WARNING]: Empty-check contradiction tests are executed without a work receipt

**File:** `src/bp_registry/canonical/impulse.py:363-369`; `src/bp_registry/canonical/interventions.py:235-237`

**Issue:** Exact-shortening impulse and freezing compute the empty-check contradiction predicate before any `BudgetTree.reserve` call. The restart implementation shows the intended treatment by reserving a `candidate_checks=1` leaf before the same predicate (`src/bp_registry/canonical/restarting.py:355-364`). The two other controllers can report `contradictory_empty_check` with no charged check, breaking cross-arm work comparability and allowing that compute after count or wall budget exhaustion.

**Fix:** Reserve and commit a named `WorkVector(candidate_checks=1)` leaf before computing the predicate. On denial, emit an attempt row whose termination is the budget/deadline result and whose contradiction value is absent; include the leaf in `phase5_work_evidence` when it was admitted.

### WR-02 [WARNING]: The sign-flip source decision uses a different qualification than the sealed executable arm

**File:** `docs/evidence/phase5-source-decisions.json:82-98`; `data/manifests/phase5-b1-mechanism-pilot.json:1240-1262`; `src/bp_registry/canonical/contracts.py:905-911`; `tests/test_phase5_public_execution.py:211-215`

**Issue:** The source-decision record calls sign flip `controlled_css_adaptation`, whereas the sealed manifest, controller identity contract, and published guide call the actual arm `bsfbp_sign_only_controlled_adaptation`. The source-record test permits only the generic value and therefore does not detect this disagreement. Qualification is a provenance field used to distinguish the sign-only adaptation from the source's compound algorithm, so a source decision cannot support the exact public arm that was run.

**Fix:** Change the sign-flip source-decision qualification to `bsfbp_sign_only_controlled_adaptation` and update its schema/test allow-list. Add a test that maps each source-decision arm to every sealed manifest arm and requires exact equality of canonical identity, source revision, qualification, and native availability.

### WR-03 [WARNING]: Restart Belief evidence claims an arXiv revision but links an unversioned mutable HTML page

**File:** `docs/evidence/phase5-source-decisions.json:100-103`

**Issue:** The evidence identifies `arXiv:2511.13281v1` but uses `https://arxiv.org/html/2511.13281`, which resolves to the current revision rather than the declared v1. A later arXiv revision can alter the cited procedure while the record continues to claim the v1 source identity.

**Fix:** Pin the source URL to `https://arxiv.org/html/2511.13281v1` and validate that any `arXiv:<id>vN` source decision uses a matching versioned URL (or records a content digest).

### WR-04 [WARNING]: Per-shot ownership is acquired only after unprotected controller computation

**File:** `src/bp_registry/canonical/execution.py:923-969`; `src/bp_registry/ledger.py:685-709`

**Issue:** `_run_phase5_structural_shot` first checks for an existing terminal row, then executes the entire controller, and only then calls `CanonicalEventWriter.begin`, which is where the per-shot owner lock is acquired. Two workers starting the same run/shot can both observe no terminal, both spend controller work, and only one gets ledger ownership. The losing worker's work is absent from the durable receipt and can exceed the one-thread/shot resource entitlement.

**Fix:** Begin the canonical writer immediately after the existing-terminal check and retain its ownership through controller execution and terminal emission. On an ownership collision, retry only by reading a completed terminal event; never dispatch a controller while another owner may be active. The deadline terminal path in CR-01 should use this same writer lifecycle.

---

_Reviewed: 2026-10-01T02:30:31Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_

## Resolution

The controller and replay fixes are in `29439d6`, `350ae2b`, `42be928`, and `a7e48bd`. They move target/order/residual computations inside reservations, charge contradiction checks, stop at declared wall-clock boundaries, preserve partial work, and replay typed deadline evidence. Shot ownership is acquired before controller dispatch. Source qualification and revision links were corrected in `9234ea4`.

The reviewer independently rechecked every flagged reserve-order and contradiction site after `a7e48bd` and found CR-01, CR-02, and WR-01 through WR-04 resolved. Public fixture-arm replay, all seven immediate-deadline replay cases, and deterministic BB-144/HGP code fixtures pass. The original B1 pilot at `5bdc3d9` remains a superseded development record; corrected work accounting requires a new calibration seal and disjoint evaluation identities before Phase 5 completion.

The replacement calibration and cap seal are retained in `6db8d3e`. All 28 calibration shots have replay-checked arm results, the self-audit passed, the 43 public Phase 5 tests passed, and the intervention design check passed 16,388 cases. The v2 evaluation uses a new physical sample namespace and decoder seeds; its matched-shot execution and replay are the remaining release checks.
