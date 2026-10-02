---
status: resolved
trigger: "Audit found Relay source preset declares SPA and label-only source procedure can pass admission without enforcing author min-sum kernel."
created: 2026-10-02
updated: 2026-10-02
---

# Symptoms

- Expected behavior: Every manifest claiming Relay's source internal BP must require the exact author's min-sum kernel and compatible procedure settings.
- Actual behavior: `RelayPreset.source_procedure()` declares SPA; contract enforcement only checks `memory_tuning`, so label-only source SPA can pass.
- Error messages: None; provenance/admission bug.
- Timeline: Found by independent audit 2026-10-02.
- Reproduction: Construct a public source-procedure manifest with SPA update and no memory_tuning; compare validation with author v0.2.2 semantics.

## Current Focus

- hypothesis: Confirmed: the source preset had the wrong profile and both manifest validators conditioned kernel enforcement on optional memory tuning.
- test: Compact and public untuned source fixtures independently vary the profile and update kind.
- expecting: Every SPA source claim is rejected; source min-sum arms with and without active tuning remain admitted.
- next_action: commit the verified fix on the isolated branch
- reasoning_checkpoint:
    hypothesis: "The SPA source claim is admitted because the preset declares SPA and kernel validation returns early whenever memory_tuning is absent."
    confirming_evidence:
      - "Pinned author v0.2.2 constructs MinSumBPDecoder in crates/relay_bp/src/bp/relay.rs."
      - "The red untuned-source fixtures were admitted before the fix, while active tuned fixtures already rejected mismatched update policies."
    falsification_test: "The hypothesis would be false if an untuned source SPA manifest were already rejected or the pinned author Relay controller used SPA."
    fix_rationale: "Bind source_internal_bp to the min-sum profile at preset/spec construction and to the min_sum update at both compact and public manifest admission, independent of tuning."
    blind_spots: "The fix does not attempt bit-for-bit native numerical equivalence or change controlled canonical_internal_bp behavior."
    candidate_causes:
      - "code: optional-memory early returns bypass source kernel validation"
      - "config: source preset persisted the canonical SPA numerical profile"
    and_gate: "yes: the preset mismatch creates bad source specs, while the independent validator loophole admits hand-built label-only manifests"

## Evidence

- timestamp: 2026-10-02T00:00:00-04:00
  checked: `RelayPreset.source_procedure`, `RelaySpecV4`, and `CanonicalManifestV4`
  found: The preset declares `cpu-float64-spa-v1`; `CanonicalManifestV4.active_relay_procedure_has_its_declared_kernel` returns immediately when `memory_tuning` is absent.
  implication: An untuned manifest can claim `source_internal_bp` while executing SPA, although pinned author v0.2.2 constructs `MinSumBPDecoder`.
- timestamp: 2026-10-02T00:01:00-04:00
  checked: focused red tests for source preset, controlled source profile, and untuned source manifest
  found: All three fail against the old code at the expected missing invariants.
  implication: Regression tests reproduce both the incorrect preset and the optional-tuning admission loophole.
- timestamp: 2026-10-02T00:02:00-04:00
  checked: compact contract fix against Relay and exact-author differential tests
  found: 26 tests pass; source SPA is rejected at profile and update-policy boundaries while untuned source min-sum remains admitted.
  implication: The compact execution contract is fixed; the same invariant must also hold in the outer public manifest contract before preflight returns.
- timestamp: 2026-10-02T00:03:00-04:00
  checked: outer `CanonicalExperimentV4` admission and held-out Relay/manifest suites
  found: Public untuned source SPA is rejected, public untuned source min-sum is admitted, and 31 Relay/Phase 4 plus 3 manifest tests pass.
  implication: The invariant holds before public preflight as well as in the compact execution contract.
- timestamp: 2026-10-02T00:04:00-04:00
  checked: revert-and-reconfirm guardrail
  found: Removing the three production hunks restores all four regression failures; reapplying them restores four passes.
  implication: The production fix, rather than a test-only change, closes the defect.

## Eliminated

- hypothesis: The wrong kernel was introduced only by the active campaign builder.
  evidence: The immutable source preset itself declared SPA, and a hand-built untuned public manifest passed the old model without using the campaign builder.
  timestamp: 2026-10-02T00:01:30-04:00

## Resolution

- root_cause: The source preset copied the canonical SPA profile, and compact/public validators enforced source kernel identity only when optional memory tuning was present.
- fix: Set the v0.2.2 source preset to the min-sum profile; reject source presets/specs with any other profile; enforce `min_sum` for every `source_internal_bp` compact and public manifest regardless of memory tuning.
- oracle_type: specified
- verification:
    target_test: {result: pass}
    mutation_check: {result: skipped, reason_if_skipped: "No Python mutation runner or Stryker configuration is present.", mutant_killed: null}
    no_op_deletion: {result: pass, deletion_justified_by_rca: false}
    adjacent_tests:
      result: pass
      suites_run:
        - "tests/canonical/test_relay.py tests/canonical/test_relay_differential.py tests/canonical/test_phase4_active_benchmark.py: 31 passed"
        - "tests/test_manifest.py -k 'canonical_v4 or phase4 or relay': 3 passed"
    revert_and_reconfirm: {result: pass, bug_returned_on_revert: true, fixed_on_reapply: true}
    guardrail_verdict: accepted
- files_changed:
    - src/bp_registry/canonical/relay.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/manifests.py
    - tests/canonical/test_relay.py
    - tests/canonical/test_phase4_active_benchmark.py
