---
status: resolved
trigger: "Independent source audit found BP-SF first-iteration flip counting and Restart Belief acceptance gate differ from source algorithms."
created: 2026-10-02
updated: 2026-10-02
---

# Symptoms

- Expected behavior: BP-SF counts flips from an all-zero previous decision on iteration one; Restart Belief uses its source-defined weight/defect gate before accepting a root BP candidate.
- Actual behavior: Syndrome flip starts previous=None, omitting the first decision; Restart Belief accepts any original-syndrome-valid root candidate regardless of its source gate.
- Error messages: None; source-semantic discrepancies.
- Timeline: Found during independent Phase-5 audit on 2026-10-02.
- Reproduction: Compare `src/bp_registry/canonical/interventions.py:457-473` with BP-SF Algorithm 1 and `src/bp_registry/canonical/restarting.py:242-257` with Restart Belief Algorithm 1, on small deterministic examples.

## Current Focus

- hypothesis: Three independent state/gate errors explain the audit findings: damping commits the raw fresh proposal, BP-SF omits the all-zero initial hard decision, and Restart Belief treats syndrome validity as sufficient for root acceptance.
- test: Add source-linked recurrence, first-iteration nonzero, and syndrome-valid overweight-root fixtures before changing implementation.
- expecting: Current code fails each source-semantic fixture; corrected code stores the damped output, counts zero-to-first transitions, and branches from overweight roots.
- next_action: complete
- reasoning_checkpoint:
    hypothesis: "Three independent code defaults cause the semantic gaps: V2C history owns the raw proposal instead of the committed output, BP-SF has no zero initial decision, and Restart root selection tests only syndrome validity."
    confirming_evidence:
      - "Primary equations/pseudocode and pinned repositories specify the opposite state or gate."
      - "Agent-authored minimal fixtures fail on the old code and pass after the corresponding changes."
    falsification_test: "The hypothesis is false if the old source hunks pass the recurrence, initial-zero, or overweight-root fixtures, or if the corrected hunks fail them."
    fix_rationale: "Commit the decoder-visible damped output, initialize BP-SF state explicitly, and separate Restart syndrome validity from a defensible weight certificate."
    blind_spots: "B1 exact distance and Restart xi remain unavailable; native end-to-end curve agreement is outside this debug task."
    candidate_causes:
      - "code: state ownership and root acceptance conditions were implemented differently from primary algorithms"
      - "data/config: B1 exposes only a distance interval and no xi, preventing the complete source defect shortcut"
    and_gate: "No for damping and BP-SF; Restart has an independent code bug plus missing source parameters, so conservative adaptation is required."

## Evidence

- timestamp: 2026-10-02T15:40:00-04:00
  observed: Gokduman--Yao--Pfister Eq. 17 uses the previous committed damped V2C message, while `V2CDamping.propose` stores `(fresh,)` and `commit` makes that raw value the next history.
  implication: Every damping trajectory diverges from the cited recurrence after the first iteration unless gamma is an endpoint or the operands coincide.
- timestamp: 2026-10-02T15:41:00-04:00
  observed: BP-SF Algorithm 1 and pinned commit 0417d33 initialize the previous hard decision to zero; the controller initializes `previous=None` and skips the first comparison.
  implication: Oscillation ranks can differ before test-vector generation.
- timestamp: 2026-10-02T15:42:00-04:00
  observed: Restart Belief Algorithm 1 gates a syndrome-valid root by `weight <= t` or the declared defect bound; the controller accepts every syndrome-valid root. B1 has only distance bounds 18--24, which prove t>=8 but do not determine the defect shortcut.
  implication: B1 can safely use weight<=8 as a conservative early-acceptance certificate and must branch for heavier roots; the defect shortcut remains unavailable without xi and exact t.
- timestamp: 2026-10-02T15:50:00-04:00
  observed: Five focused regression nodes produced six failures before implementation: two damping parameter cases, the multi-step damping history, BP-SF initial counting, and both B1/exact-distance Restart gates.
  implication: The new fixtures distinguish all three audited semantic errors from prior behavior.
- timestamp: 2026-10-02T15:55:00-04:00
  observed: After implementation the same focused selection passes 7/7, including damping endpoints, multi-step recurrence, initial-zero oscillation counts, and overweight valid-root branching.
  implication: Each local root cause is corrected; broader integration and replay validation remain.
- timestamp: 2026-10-02T16:05:00-04:00
  observed: The import-graph and public replay selection passed 176 tests under the manifest-required OMP_NUM_THREADS=1; an additional memory-composition, factorial, and canonical-CLI selection passed 90 tests. The independent intervention algebra validator passed 16,384 shortening cases and four constructed cases.
  implication: Adjacent memory schedules, all Phase 5 intervention families, public ledger reconstruction, and algebraic lifts remain compatible with the fixes.
- timestamp: 2026-10-02T16:12:00-04:00
  observed: Reversing only the three production-code hunks restored six focused failures; reapplying them restored an 8/8 focused pass including the B1 threshold endpoint.
  implication: The corrected production hunks, rather than weakened tests or unrelated changes, cause the semantic fixes.

## Eliminated

## Resolution

- root_cause: "V2C history committed the raw fresh proposal instead of the damped output; BP-SF omitted the source all-zero initial hard decision; Restart Belief conflated syndrome validity with source early acceptance."
- fix: "Store the committed damped V2C output, count BP-SF transitions from zero, and apply an evidence-bearing conservative Restart weight gate (exact t where known, proven t>=8 for B1) while marking the xi defect shortcut unavailable."
- oracle_type: specified
- verification:
    target_test: {result: pass}
    mutation_check: {result: skipped, reason_if_skipped: "No Python mutation framework is configured; direct hunk reversal was used instead.", mutant_killed: null}
    no_op_deletion: {result: pass, deletion_justified_by_rca: false}
    adjacent_tests:
      result: pass
      suites_run:
        - "176 memory, intervention, code-fixture, and public replay tests"
        - "90 memory-composition, Phase 4 factorial, and canonical CLI tests"
        - "16,384 shortening cases and four constructed algebra cases"
    revert_and_reconfirm: {result: pass, bug_returned_on_revert: true, fixed_on_reapply: true}
    guardrail_verdict: accepted
- files_changed:
    - src/bp_registry/canonical/memory.py
    - src/bp_registry/canonical/interventions.py
    - src/bp_registry/canonical/restarting.py
    - tests/canonical/test_memory_execution.py
    - tests/canonical/test_memory_policies.py
    - tests/canonical/test_phase5_damping.py
    - tests/canonical/test_perturbative_interventions.py
    - tests/canonical/test_restart_execution.py
    - docs/canonical-engine.md
    - docs/memory-policy-sources.md
    - docs/phase5-interventions.md
    - docs/evidence/phase5-source-decisions.json

## Prevention

- why_not_caught: "Unit tests asserted damping against previous fresh history, BP-SF tests did not use a first nonzero hard decision, and Restart tests did not include a valid root above t. Same-code replay therefore reproduced the deviations instead of detecting them."
- recurrence_guard: "Source-linked multi-step, initial-zero, and threshold-boundary tests now fail on the prior hunks and pass on the correction; public replay and algebra suites remain required."
- causal_branches:
    - "Code/state branch: policy history did not distinguish raw proposals from committed decoder-visible values."
    - "Evidence/config branch: B1's interval distance and missing xi were not represented at root selection, allowing an unconditional validity shortcut."
