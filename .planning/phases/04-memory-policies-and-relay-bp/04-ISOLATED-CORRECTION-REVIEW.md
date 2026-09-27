---
phase: 04-memory-policies-and-relay-bp
reviewed: 2026-09-27T02:39:54Z
scope: isolated committed correction and notebook slices only
reviewed_commits: [fc214ef, 0986a0f, 45a286e, 5136b43]
excluded: [4e7e7b9, uncommitted local changes, main calibration checkout]
depth: deep
files_reviewed: 12
files_reviewed_list:
  - src/bp_registry/canonical/contracts.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/memory_execution.py
  - src/bp_registry/canonical/verification.py
  - src/bp_registry/canonical/updates.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - src/bp_registry/canonical/memory.py
  - scripts/phase4_notebook_support.py
  - scripts/execute_phase4_notebook.py
  - notebooks/phase4-memory-relay-analysis.ipynb
  - tests/canonical/test_memory_execution.py
findings:
  critical: 4
  warning: 0
  info: 0
  total: 4
status: issues_found
---

# Phase 4 isolated correction-slice review

**Scope:** This is an interim adversarial review of the stable committed correction and notebook-scaffold slices in the isolated checkout. It is not a Phase 4 completion, goal, or notebook-production verdict. The explicitly labelled absence of production adapters and quantitative notebook views is not a finding.

## Blockers

### CR-01: Public disordered assignments reuse one graph-level stream for every shot

**Classification:** **BLOCKER**

**Files:** `src/bp_registry/canonical/execution.py:987`, `src/bp_registry/canonical/memory_execution.py:95-96`, `src/bp_registry/canonical/memory_execution.py:145-148`, `src/bp_registry/canonical/memory_execution.py:173-176`, `src/bp_registry/canonical/verification.py:588`

**Failing scenario:** Run a V4 memory-only manifest with a uniform affine-prior assignment for shots 0 and 1 on the same code. Public execution creates `MemoryFloodingSchedule` without an identity context. The schedule therefore falls back to graph-derived `configuration_identity` and `decoder_identity`; its draw seed and `replay_identity` are identical for a given source iteration in both shots. The semantic verifier recreates the same graph-only context, so it verifies this unintended cross-shot reuse.

**Issue:** The committed public path does not give each decoder attempt its own purpose-separated assignment identity, despite the declared decoder-local assignment/replay semantics. Independent shots consequently use the same disordered coefficient vector at every source iteration, and the ledger cannot distinguish the intended per-shot assignment stream.

**Fix:** Pass non-trace `configuration_identity` and shot/attempt-specific `decoder_identity` values when creating `MemoryFloodingSchedule` in both execution and semantic replay. Derive them from the already available public manifest/execution identity, never hidden truth. Add public tests proving same-shot replay equality, cross-shot coefficient inequality, and equality between traced and trace-off execution.

### CR-02: Ordinary V3 source-iteration min-sum policies are executed and replayed at the wrong index

**Classification:** **BLOCKER**

**Files:** `src/bp_registry/canonical/execution.py:316-324`, `src/bp_registry/canonical/verification.py:603-615`, `src/bp_registry/canonical/updates.py:420-424`, `src/bp_registry/manifests.py:640-650`

**Failing scenario:** Use an ordinary (non-memory) V3 flooding manifest with `offset_min_sum` and `parameter_assignment={"shape":"source_iteration","values":[0.0, 5.0]}`. The executor checks only `update_rule.alpha`, which does not exist on `OffsetMinSumUpdate`, and calls `FloodingSchedule.sweep()` without `source_iteration`; every sweep therefore receives its default of zero and uses `values[0]`. The semantic replayer also supplies `source_iteration` only for V5 memory, so it falsely validates the same all-zero-index calculation. For ordinary source-iteration NMS, execution advances the index but the replayer does not, so a multi-iteration record can fail semantic verification. Preflight also lacks a V3 length check, permitting a short NMS sequence to fail mid-shot rather than before artifact loading.

**Issue:** Published source-iteration update assignments do not have a consistent public dispatch, replay, or admission contract outside the memory route. This can produce validated evidence for the wrong OMS calculation or leave a partial, unterminated ledger for short NMS assignments.

**Fix:** Detect both `alpha` and `beta` source-iteration assignments in the executor, pass the source iteration through all ordinary flooding replay paths, and reject any source-iteration assignment shorter than the declared attempt limit during V3/V4 preflight. Add separate ordinary NMS and OMS multi-iteration dispatch/replay fixtures plus short-assignment preflight tests.

### CR-03: The notebook index can relabel a qualified snapshot as another research stage

**Classification:** **BLOCKER**

**File:** `scripts/phase4_notebook_support.py:162-167`

**Failing scenario:** Build a digest-valid `index.json` whose `stages["evaluation"]` is a valid, producer-qualified baseline identity. `notebook_inventory()` checks the index digest and section-key set, then calls `load_stage()` with that baseline identity. `load_stage()` validates the baseline snapshot and returns it under the `evaluation` key. The notebook displays that record in the evaluation cell.

**Issue:** Index keys are not bound to the identity's own `facts.stage`, allowing otherwise valid evidence to be misattributed across notebook sections.

**Fix:** Before calling `load_stage`, require each indexed identity to be structurally valid and to declare the same stage as its index key. Add a test with two valid identities swapped in a self-consistent index and require rejection.

### CR-04: Memory-operation evidence undercounts two-array histories

**Classification:** **BLOCKER**

**Files:** `src/bp_registry/canonical/memory_execution.py:332-338`, `src/bp_registry/canonical/memory.py:217-222`, `src/bp_registry/canonical/memory.py:302-309`

**Failing scenario:** Run one committed PD-prime or posterior-momentum sweep on an `n`-variable graph. PD-prime commits both its field and per-variable C2V history; momentum commits both posterior and velocity. Each is two `n`-element history arrays, but `memory_element_updates` reports only `n` for either binding.

**Issue:** Terminal memory-work provenance claims a smaller number of vector-element updates than the execution commits. This makes comparisons that consume the declared memory-operation evidence scientifically incorrect even though BP directional work remains separate.

**Fix:** Count every committed history array per binding (or track exact per-sweep memory-operation deltas transactionally). PD-prime and momentum should each report two variable-vector updates per committed sweep; retain the separate PD-prime reduction-addition count. Add exact count assertions for every memory policy kind.

---

_Reviewed only stable committed sources through `5136b43`; no source, test, notebook, main-checkout, or calibration state was changed._

## Bounded correction recheck — 2026-09-27

**Interim verdict:** The four blockers above are resolved in the bounded follow-up commits `3743d35` (public execution, replay, trace, and memory accounting) and `9e4c078` (notebook stage binding). This remains an interim correction-slice recheck, not a final Phase 4 quality, completion, or goal verdict.

### CR-01 — resolved

`PublicShotContext.memory_execution_context` derives a configuration key and a shot-specific decoder key without trace-plan fields or ledger paths (`src/bp_registry/canonical/verification.py:349-377, 424-432`). The public runner injects that context into execution (`src/bp_registry/runner.py:330-350`); the semantic replayer reconstructs the same context (`src/bp_registry/canonical/verification.py:653-658`). `MemoryFloodingSchedule` now keeps the execution and trace contexts separate, so tracing cannot supply the PCG64 assignment key (`src/bp_registry/canonical/memory_execution.py:94-121`). The focused public trace test checks trace-on/off equality, same-context replay, and distinct replay identities for shots 0 and 1 (`tests/canonical/test_memory_trace.py:107-143`).

### CR-02 — resolved

Both public execution and independent replay select either `alpha` or `beta` before forwarding a `source_iteration` assignment (`src/bp_registry/canonical/execution.py:302-324`, `src/bp_registry/canonical/verification.py:673-686`). V3-family preflight rejects an assignment shorter than `attempt.max_iterations` before artifact loading (`src/bp_registry/manifests.py:661-670`). Focused NMS and OMS multi-iteration dispatch/replay and early-rejection tests cover the two rule variants (`tests/canonical/test_memory_execution.py:382-422`).

### CR-03 — resolved

`notebook_inventory()` now requires every index entry to contain identity facts whose declared `stage` equals the index key before it loads the snapshot (`scripts/phase4_notebook_support.py:167-172`). The adversarial baseline-as-evaluation index is rejected by the focused test (`tests/canonical/test_phase4_notebook.py:117-127`).

### CR-04 — resolved

Ordinary-memory evidence now counts two variable histories for `pdprime_delta_mix` and `posterior_momentum` (`src/bp_registry/canonical/memory_execution.py:336-345`), and the semantic verifier independently derives the same binding width (`src/bp_registry/canonical/verification.py:699-721`). The focused direct schedule check asserts `2 * variable_count` after one committed sweep for both policy kinds (`tests/canonical/test_memory_execution.py:425-434`).

This recheck was static review of the named stable commits and their focused test additions. No test command was run, no source was changed, and active factorial/preparation work was excluded.
