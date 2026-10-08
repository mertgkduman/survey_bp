---
phase: 10-correlated-quaternary-execution
reviewed: 2026-10-08T04:14:34Z
depth: standard
files_reviewed: 47
files_reviewed_list:
  - data/fixtures/quaternary/asced-gb46-canonical-fixture.json
  - data/fixtures/quaternary/asced-gb46-canonical-overcomplete-map.json
  - data/manifests/quaternary-five-qubit-tracer.json
  - data/manifests/quaternary-gb46-asced.json
  - data/manifests/quaternary-gb46-bp4.json
  - data/native/phase10-asced-build-receipt.json
  - data/native/phase10-asced-run-receipt.json
  - data/native/phase10-asced-source-spec.json
  - data/studies/phase10-quaternary-b1-gate.json
  - scripts/qualify_phase10_native_asced.py
  - scripts/run_phase10_quaternary_gate.py
  - src/bp_registry/cli.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - src/bp_registry/quaternary/__init__.py
  - src/bp_registry/quaternary/algebra.py
  - src/bp_registry/quaternary/asced.py
  - src/bp_registry/quaternary/asced_overcomplete.py
  - src/bp_registry/quaternary/compatibility.py
  - src/bp_registry/quaternary/contracts.py
  - src/bp_registry/quaternary/evaluator.py
  - src/bp_registry/quaternary/execution.py
  - src/bp_registry/quaternary/kernel.py
  - src/bp_registry/quaternary/mbp4.py
  - src/bp_registry/quaternary/native_asced.py
  - src/bp_registry/quaternary/numerics.py
  - src/bp_registry/quaternary/problems.py
  - src/bp_registry/quaternary/qbpgd.py
  - src/bp_registry/quaternary/sampling.py
  - src/bp_registry/quaternary/schedules.py
  - tests/canonical/quaternary/__init__.py
  - tests/canonical/quaternary/conftest.py
  - tests/canonical/quaternary/fixtures/asced-overcomplete.json
  - tests/canonical/quaternary/fixtures/asced-splitters.json
  - tests/canonical/quaternary/test_algebra.py
  - tests/canonical/quaternary/test_asced_ensemble.py
  - tests/canonical/quaternary/test_asced_evidence.py
  - tests/canonical/quaternary/test_asced_overcomplete.py
  - tests/canonical/quaternary/test_asced_splitters.py
  - tests/canonical/quaternary/test_bpgd.py
  - tests/canonical/quaternary/test_evaluator.py
  - tests/canonical/quaternary/test_kernel.py
  - tests/canonical/quaternary/test_mbp4.py
  - tests/canonical/quaternary/test_public_execution.py
  - tests/canonical/quaternary/test_sampling.py
  - tests/canonical/quaternary/test_schedules.py
  - tests/canonical/quaternary/test_vector_oracle.py
findings:
  critical: 4
  warning: 2
  info: 0
  total: 6
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-10-08T04:14:34Z  
**Depth:** standard  
**Files Reviewed:** 47  
**Status:** issues_found

## Summary

The review traced the public quaternary execution path, policy compatibility path, canonical evidence verifier, and native aSCED receipt path. The implementation accepts and records configurations and provenance claims that it does not execute or independently verify. This invalidates policy-comparison and native-evidence claims until the blockers below are resolved. Generated Phase 10 ledgers were excluded from the review scope.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: BLOCKER — public scalar-policy compositions are recorded without being executed

**File:**
[`src/bp_registry/runner.py:267`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/runner.py:267), [`src/bp_registry/quaternary/execution.py:288`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/execution.py:288), [`src/bp_registry/quaternary/compatibility.py:64`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/compatibility.py:64), [`src/bp_registry/quaternary/schedules.py:162`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/schedules.py:162)

**Issue:** Compatibility accepts scalar `qbp_flooding` and `qbp_variable_serial` schedules and check transforms, and the resolved composition is written to the ledger. In the scalar qBPGD path, the public runner passes neither schedule nor transforms into execution: it constructs a plain `ScalarLlrBp4Kernel` session and the controller calls that session's default `sweep()`. In the V2 tracer path, the runner merely appends the resolved composition to an already-created fixed-flooding ledger. `run_quaternary_asced()` maps an MBP4 schedule into `Mbp4Spec`, but still does not construct or apply a check transform. The only production uses of `QbpFloodingSchedule`, `QbpVariableSerialSchedule`, and `QuaternaryCheckTransform` are inside `schedules.py`; no public scalar execution path constructs them. A compatible scalar-policy manifest can therefore pass preflight and produce a ledger that claims a schedule or normalization policy while ordinary flooding BP ran.

**Fix:** Convert the accepted policy specifications into typed schedule and transform objects at the public execution boundary, validate their required parameters, and make every compatible controller execute through that schedule. Reject a composition if its schedule or transforms cannot be executed by that kernel. For example, refactor qBPGD to accept an executable sweep policy instead of calling `session.sweep()` directly:

```python
schedule = build_qbp_schedule(composition.schedule, composition.transforms, session)
decoded = controller.run(sweep_once=schedule.sweep)
```

Then add public-runner tests whose decoded messages or decision differ between flooding and variable-serial/normalized configurations, rather than only asserting ledger metadata.

### CR-02: BLOCKER — V2 manifests promise a multi-shot budget but the public runner always runs shot zero

**File:**
[`src/bp_registry/manifests.py:765`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/manifests.py:765), [`src/bp_registry/runner.py:248`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/runner.py:248), [`src/bp_registry/runner.py:267`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/runner.py:267), [`src/bp_registry/runner.py:312`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/runner.py:312)

**Issue:** V2 permits every `shot_budget` from 1 through `MAX_SHOT_BUDGET`, but `run_manifest_shot()` rejects every `shot_id` except `0` and calls all three execution functions with the literal `shot_id=0`. The verifier also always replays zero. As a result, a V2 manifest with a budget greater than one cannot run or replay its declared shots; the only evidence row is a static manifest problem labelled as shot zero. This makes the declared budget and any multi-shot statistical interpretation false.

**Fix:** Either constrain V2 to a single-shot manifest (`shot_budget: Literal[1]`) or implement the contract: derive the selected shot's observation from the deterministic sampler, propagate the validated requested ID through execution and verification, and record it. A guard should accept the full declared range:

```python
if shot_id is None or not 0 <= shot_id < manifest.shot_budget:
    raise ValueError("shot_id is outside this manifest's shot budget")
return run_quaternary_qbpgd(..., shot_id=shot_id)
```

Add a test for a two-shot V2 manifest that produces and independently replays both IDs.

### CR-03: BLOCKER — the canonical evidence verifier can approve a fabricated decoder ledger

**File:**
[`scripts/run_phase10_quaternary_gate.py:251`](/hpc/home/mg551/storage/survey_bp/scripts/run_phase10_quaternary_gate.py:251), [`scripts/run_phase10_quaternary_gate.py:267`](/hpc/home/mg551/storage/survey_bp/scripts/run_phase10_quaternary_gate.py:267), [`scripts/run_phase10_quaternary_gate.py:295`](/hpc/home/mg551/storage/survey_bp/scripts/run_phase10_quaternary_gate.py:295)

**Issue:** `verify` recomputes an event ID from each event's supplied content, checks that supplied candidates match the original syndrome, and checks internal outcome flags. It never reruns `ScalarLlrBp4Kernel`, `AscedController`, or the overcomplete controller and never compares the resulting terminal state, candidate, work, or path records to the ledger. An editor can replace each candidate with any Pauli having the same syndrome, choose matching outcome flags and a nonempty work dictionary, recompute event IDs and the ledger SHA in the study receipt, and get a passing verification. The retained canonical ledger therefore does not prove that the reported decoder generated its reported paths or work.

**Fix:** Make verification reproduce the frozen batch and run the exact ordinary and overcomplete controllers for every shot. Compare all security-relevant and scientific-result fields, including terminal state, candidate, work/counters, virtual-candidate ordering, selected origin, and per-path results. Share a single event-construction function between `run` and `verify`, with `verify` deriving expected records from execution rather than from submitted event values.

### CR-04: BLOCKER — a forged native-success receipt is accepted as native aSCED evidence

**File:**
[`src/bp_registry/quaternary/native_asced.py:81`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/native_asced.py:81), [`scripts/qualify_phase10_native_asced.py:415`](/hpc/home/mg551/storage/survey_bp/scripts/qualify_phase10_native_asced.py:415), [`scripts/run_phase10_quaternary_gate.py:135`](/hpc/home/mg551/storage/survey_bp/scripts/run_phase10_quaternary_gate.py:135)

**Issue:** The native-receipt checks require a matching source-spec digest, commit, Pauli ordering, terminal string, and a positive trial count. They do not load and hash the claimed build receipt, validate source digests or native commands, validate the run command/configuration, or check basic result arithmetic such as `0 <= logical_errors <= trials`. A hand-written run receipt with `terminal: "native_success"`, the public source-spec digest, a positive `trials` value, and arbitrary metric values is accepted by both the library and the Phase 10 gate without a native build or run.

**Fix:** Verify the run receipt against the actual build receipt and source spec, recomputing `build_receipt_sha256`; validate the successful build/run command records and source snapshots; and validate all aggregate constraints before creating metric facts. At minimum:

```python
assert sha256_file(build_receipt_path) == run["build_receipt_sha256"]
assert 0 <= run["logical_errors"] <= run["trials"]
assert run["failures"] + run["successes"] == run["trials"]
assert run["command"]["config"] == expected_native_config
```

Bind an immutable external build/run artifact (or its independently stored digest) if the receipt itself must provide tamper-resistant provenance.

## Warnings

### WR-01: WARNING — aSCED's MBP4 branch can exceed the BP-work limit that its controller preflights

**File:**
[`src/bp_registry/quaternary/asced.py:509`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/asced.py:509), [`src/bp_registry/quaternary/asced.py:531`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/asced.py:531), [`src/bp_registry/quaternary/mbp4.py:298`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/mbp4.py:298)

**Issue:** aSCED preflights each attempted branch as `AscedSpec.max_iterations` BP calls, then its MBP4 branch creates a session and calls `session.run()` with no controller cap. The MBP4 session instead runs to `Mbp4Spec.max_iterations`. Public manifest execution happens to construct equal limits, but the exported `AscedController` accepts independent specs. A caller with an MBP4 limit above the aSCED limit can exceed `max_total_bp_calls` despite the preflight and publish an understated work count.

**Fix:** Require the two limits to be equal when constructing an MBP4 aSCED controller, or add a `max_iterations` argument to MBP4 session execution and pass `AscedSpec.max_iterations`. Account from the actual completed MBP4 iterations and add a regression case with mismatched specs.

### WR-02: WARNING — a normal test invokes a destructive, network-dependent native build

**File:**
[`tests/canonical/quaternary/test_asced_evidence.py:124`](/hpc/home/mg551/storage/survey_bp/tests/canonical/quaternary/test_asced_evidence.py:124), [`scripts/qualify_phase10_native_asced.py:179`](/hpc/home/mg551/storage/survey_bp/scripts/qualify_phase10_native_asced.py:179), [`scripts/qualify_phase10_native_asced.py:227`](/hpc/home/mg551/storage/survey_bp/scripts/qualify_phase10_native_asced.py:227)

**Issue:** The test calls the real `build` command with no integration marker, mock, or unique temporary root. The command removes checkout/venv paths under the fixed `/tmp/phase10-asced-native` root and then downloads, builds, and installs external dependencies. Ordinary test runs can fail when network/toolchain access is unavailable and concurrent runs can delete each other's build directory, making the test suite unreliable.

**Fix:** Move this case behind an explicitly selected integration/network marker and give each integration run a caller-provided unique temporary work root. Unit-test the command and receipt-validation logic with mocked subprocess/network operations; run the real build only in a provisioned native integration job.

---

_Reviewed: 2026-10-08T04:14:34Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
