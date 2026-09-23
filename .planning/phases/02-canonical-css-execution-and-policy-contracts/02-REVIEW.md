---
phase: 02-canonical-css-execution-and-policy-contracts
reviewed: 2026-09-23T09:57:23Z
depth: standard
files_reviewed: 40
files_reviewed_list:
  - .gsd/tdd-evidence/02-07-task-1-red.json
  - .gsd/tdd-evidence/02-07-task-2-red.json
  - data/manifests/canonical-three-qubit-development.json
  - data/manifests/schema-canonical-v2.json
  - data/results/canonical-three-qubit-development/events.jsonl
  - data/results/canonical-three-qubit-development/result.json
  - docs/canonical-engine.md
  - docs/profiling-and-tracing-strategy.md
  - docs/research-novelty-and-depth-register.md
  - src/bp_registry/canonical/__init__.py
  - src/bp_registry/canonical/budgets.py
  - src/bp_registry/canonical/contracts.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/kernel.py
  - src/bp_registry/canonical/lineage.py
  - src/bp_registry/canonical/metrics.py
  - src/bp_registry/canonical/numerics.py
  - src/bp_registry/canonical/problems.py
  - src/bp_registry/canonical/profiling.py
  - src/bp_registry/canonical/schedules.py
  - src/bp_registry/canonical/tracing.py
  - src/bp_registry/cli.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/reference.py
  - src/bp_registry/runner.py
  - tests/canonical/conftest.py
  - tests/canonical/test_budgets.py
  - tests/canonical/test_contracts.py
  - tests/canonical/test_flooding.py
  - tests/canonical/test_numerics.py
  - tests/canonical/test_policy_evidence.py
  - tests/canonical/test_profiling.py
  - tests/canonical/test_tracing.py
  - tests/canonical/test_truth_boundary.py
  - tests/canonical/test_work_accounting.py
  - tests/fixtures/canonical-semantic-events.json
  - tests/test_canonical_cli.py
  - tests/test_ledger.py
  - tests/test_reference_smoke.py
findings:
  critical: 4
  warning: 7
  info: 0
  total: 11
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-23T09:57:23Z
**Depth:** standard
**Files Reviewed:** 40
**Status:** issues_found

## Summary

The new kernel and its unit contracts are substantial, and the focused suite passes (`67 passed`). That suite does not exercise the public canonical path as a policy-driven, budget-enforced, profiled/traced engine. The submitted result therefore overstates several guarantees: persisted policy choices do not control execution, declared work limits are not applied, and a BP call is reported as zero work. The structural ledger also permits a non-owner to append forged intermediate provenance.

## Narrative Findings (AI reviewer)

All findings below were independently verified against the current source and checked fixture.

## Critical Issues

### CR-01 [BLOCKER]: Persisted policy composition is validated but never dispatched into canonical execution

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:120`

**Issue:** `_canonical_kernel_manifest()` serializes the policy data, but `run_canonical_structural_shot()` merely resolves it and calls `PolicyRuntime(...).traverse_lifecycle()` at [execution.py:295](../../../src/bp_registry/canonical/execution.py). It then unconditionally invokes `BinarySpaKernel().run()` at [execution.py:314](../../../src/bp_registry/canonical/execution.py). No policy handler is resolved or called; `capability_view()` and `apply_decision()` have no production caller. Consequently valid changes to update, schedule, stopping, selection, or state-memory bindings alter the persisted `policy_identity` without changing the kernel behavior, termination, or selection. This makes policy-labelled comparisons scientifically uninterpretable.

**Fix:** Resolve each allowed binding to a concrete engine-owned policy implementation and make the canonical executor invoke it at its declared hook, validating and recording each decision. Until that exists, reject every composition except the one fixed baseline instead of accepting labels that have no runtime effect. Add integration tests proving that each supported non-identity binding either changes its declared behavior/evidence or is rejected as unsupported.

### CR-02 [BLOCKER]: Public count/work budgets are never enforced before canonical work

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:120`

**Issue:** The public manifest contains `shot`, `search`, and `attempt` `max_work_units` limits, but `_canonical_kernel_manifest()` retains only `attempt.max_iterations`. The structural runner directly calls the kernel at [execution.py:314](../../../src/bp_registry/canonical/execution.py) and only constructs a `WorkVector` after it returns at [execution.py:330](../../../src/bp_registry/canonical/execution.py). `AtomicFloodingExecutor` contains reservation logic, but has no production call site. A canonical run can therefore exceed a declared work cap before it is observed, contradicting the hard reserve-before-mutation contract and invalidating controlled-work comparisons.

**Fix:** Translate the manifest's scoped budget declaration into a resource-specific `BudgetTree`, reserve the complete sweep vector before `FloodingSchedule.sweep`, commit only after a finite buffer swap, and emit the binding-scope termination when reservation fails. Replace the undefined scalar `max_work_units` with declared `WorkVector` resource caps (or define and implement its conversion). Add an end-to-end test whose cap is smaller than one sweep and asserts no mutation/work commit occurs.

### CR-03 [BLOCKER]: Checked evidence reports zero BP calls even though each attempt invokes the BP kernel

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:314`

**Issue:** Every structural attempt calls `BinarySpaKernel().run()`, but its emitted vector is built exclusively with `WorkVector.from_flooding_counts()` at [execution.py:330](../../../src/bp_registry/canonical/execution.py), which leaves `bp_calls` at its default zero ([budgets.py:46](../../../src/bp_registry/canonical/budgets.py)). The checked ledger records `bp_calls: 0` for both completed attempts at [events.jsonl:5](../../../data/results/canonical-three-qubit-development/events.jsonl:5). This is a false work claim in the durable evidence and defeats comparisons that use BP-call accounting.

**Fix:** Account for one `bp_calls` unit per canonical kernel attempt (separately from per-sweep message work), and ensure that it is included in the corresponding budget reservation and terminal vector. Add an integration assertion over the checked structural ledger.

### CR-04 [BLOCKER]: A writer that does not own a shot can inject structural provenance events

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/ledger.py:535`

**Issue:** `CanonicalEventWriter.event()` routes directly to `_append()` without checking `self._owners[(run_id, shot_id)]`. `_append()` only checks that some `shot_begin` is open ([ledger.py:500](../../../src/bp_registry/ledger.py)); it does not verify the writer holds that shot's advisory lock. A second process can thus append forged `candidate`, `selection`, `work`, or other intermediate facts while the legitimate owner runs. I reproduced this with a separate `CanonicalEventWriter`: the resulting valid sequence was `shot_begin`, forged `candidate`, `termination`. Since canonical verification reconstructs mainly from terminal rows, this injected structural evidence is not rejected.

**Fix:** Require an active owner handle for every non-begin event, make `event()` reject lifecycle kinds reserved for `begin()`/`terminal()`, and retain the ownership lock through the append/fsync. Add a multi-writer test that attempts an intermediate event from a non-owner and expects `ShotOwnershipError`.

## Warnings

### WR-01 [WARNING]: A failing profiled action leaves global `tracemalloc` enabled

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/profiling.py:409`

**Issue:** `measure()` starts allocation tracing before entering the `try`, but calls `_allocation_end()` only after the `try` block. If `action()` raises, Python propagates after the `finally` at lines 419-421 and skips lines 422-442, so `_allocation_end()` never calls `tracemalloc.stop()` when this profiler started it. This leaks global instrumentation into later runs and changes their memory/runtime measurements. A direct reproduction with `track_python_allocations=True` followed by a raising action left `tracemalloc.is_tracing()` equal to `True`.

**Fix:** Finalize allocation tracing in an outer `finally`, while preserving the action exception (for example, capture the exception, call `_allocation_end()`, then re-raise). Add a regression test that verifies tracing is off after a failing action that the profiler started.

### WR-02 [WARNING]: Replay population eligibility is not bound to the selected cohort identity

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/profiling.py:209`

**Issue:** `ReplayLink` stores both `sample_identity` and `cohort.run_identity`, but validates neither relationship. `population_estimate_eligible` at line 253 only checks the cohort label and semantic agreement. A representative cohort selected for `sample-7` can be linked to a different sample and still be declared eligible; this was reproduced with equal semantic dictionaries and returned `True`. The current test itself supplies a `sample-7` cohort to a divergent `sample-8` link at [test_profiling.py:127](../../../tests/canonical/test_profiling.py), masking the missing invariant.

**Fix:** Define the cohort identity unambiguously (sample or paired run) and require it to equal the corresponding replay identity in `ReplayLink.__post_init__`. Add a test that a mismatched identity is rejected before population eligibility can be queried.

### WR-03 [WARNING]: Trace and profiling plans are accepted by the public manifest but ignored by the runner

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:120`

**Issue:** The public `CanonicalExperimentV2` requires `trace_plan` and `profile_plan`, yet the compact manifest passed to the executor omits both. There is no production instantiation of `TracePlan`, `TraceSink`, or `LocalProfiler`; the structural path only emits an ad hoc wall-clock event and device-timer missingness at [execution.py:336](../../../src/bp_registry/canonical/execution.py). Thus a manifest declaring full/filtered tracing or profiling enabled is accepted but produces neither the requested sidecar/link nor typed profiling evidence, while docs describe these as execution controls.

**Fix:** Materialize and pass those plans into canonical execution, invoke them observationally, and write their typed evidence/links. If that work is deferred, reject all unsupported non-default plan configurations at preflight. Add end-to-end tests for `off` versus enabled tracing and enabled versus disabled profiling.

### WR-04 [WARNING]: The tutorial states the opposite check matrix from the implemented X-error syndrome

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/docs/canonical-engine.md:96`

**Issue:** The tutorial says the observed syndrome is `s = Hx (mod 2)`. The implementation samples a Z-check syndrome as `Hz @ hidden_x` ([sampling.py:105](../../../src/bp_registry/sampling.py)) and sends `validated.hz` to the canonical kernel ([execution.py:314](../../../src/bp_registry/canonical/execution.py)). Following the published equation would therefore produce a different syndrome convention from the executable fixture. The anchor-only test also codifies the erroneous `s = hx (mod 2)` string at [test_policy_evidence.py:16](../../../tests/canonical/test_policy_evidence.py).

**Fix:** Correct the tutorial and its test to the explicit convention actually implemented, e.g. `s_Z = H_Z e_X (mod 2)` for X-error recovery, or change the implementation only if the intended convention is genuinely the other one.

### WR-05 [WARNING]: Candidate lineage silently coerces fractional payloads into different binary recoveries

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/lineage.py:167`

**Issue:** `_payload_tuple()` applies `int(value)` before verifying membership in `{0, 1}`. It accepts fractional or numeric-string inputs and hashes the coerced result instead of rejecting malformed candidate evidence. For example, `[0.9, 1.1]` is accepted and retained as `(0, 1)`. This silently changes the recovery represented by a content-addressed lineage record.

**Fix:** Validate the original payload dtype/value first: require one-dimensional integer (non-boolean) values equal to 0 or 1, then convert to Python integers. Add rejection tests for floats, strings, booleans, and non-vector shapes.

### WR-06 [WARNING]: Selection accepts a candidate detached from the current original/working lineage

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/execution.py:243`

**Issue:** A custom selection policy can return any `OriginalSpaceCandidate`. `select_stable_candidate()` only sorts it; neither the engine nor `OriginalSpaceCandidate` verifies that `candidate.working is working`, that its lineage derives from this attempt, or even that `WorkingProblem.parent_edge` names its own child/relation ([problems.py:41](../../../src/bp_registry/canonical/problems.py)). The engine then evaluates the payload against the real code while recording the supplied, potentially unrelated candidate lineage. This breaks the claimed immutable original→working→candidate provenance chain.

**Fix:** At the engine boundary reject candidates whose working problem and typed parent edge do not match the current attempt; make `WorkingProblem` validate the relation and child ID, and derive/verify candidate IDs from the current working ID plus canonical payload. Add a hostile-policy regression test returning a same-length candidate from another working problem.

### WR-07 [WARNING]: Canonical commands still require the native `ldpc` package

**File:** `/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/runner.py:19`

**Issue:** The canonical CLI imports `runner`, which imports `reference`, and `reference.py` imports `ldpc.BpDecoder` at module import time. In addition, canonical preflight calls `_actual_environment()`, which unconditionally asks for `version("ldpc")` at [manifests.py:383](../../../src/bp_registry/manifests.py). A project-owned canonical kernel therefore cannot run in the deliberately separate canonical environment unless the native reference dependency is installed, contrary to the documented architecture separation.

**Fix:** Lazy-import the native adapter only inside the legacy/native execution path, and make canonical environment verification query only Python/NumPy/SciPy. Add a canonical preflight/run test in an environment where `ldpc` is unavailable.

---

_Reviewed: 2026-09-23T09:57:23Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
