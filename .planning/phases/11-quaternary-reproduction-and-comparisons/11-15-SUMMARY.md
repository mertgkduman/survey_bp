---
phase: 11-quaternary-reproduction-and-comparisons
plan: "15"
subsystem: controlled evaluation authorization and evidence closure
tags: [GB46, BB72, quaternary, authorization, zero-dispatch, provenance]
requires:
  - phase: 11-09
    provides: bounded GB46 matched controlled lifecycle
  - phase: 11-10
    provides: BB72 qualification and default-deny dispatch package
  - phase: 11-11
    provides: sealed owner-reviewed preserve-deny authorization receipt
provides:
  - Code-specific immutable GB46 and BB72 zero-dispatch controlled-evaluation receipts
  - Fail-closed authorization consumer and public preflight, close, resume, and verification CLI
  - Independent two-code receipt verification with no assessment-ready calibration evidence
affects: [11-14, quaternary-controlled-comparisons, publication-assessment]
tech-stack:
  added: []
  patterns: [digest-bound terminal closure, code-specific receipt validation, calibration evidence separation]
key-files:
  created:
    - src/bp_registry/campaigns/controlled_evaluation.py
    - scripts/run_phase11_controlled_evaluation.py
    - data/results/phase11-controlled-evaluation/gb46/evaluation-receipt.json
    - data/results/phase11-controlled-evaluation/bb72/evaluation-receipt.json
    - data/results/phase11-controlled-evaluation/verification.json
    - tests/test_phase11_controlled_evaluation.py
  modified: []
key-decisions:
  - "The sealed preserve-deny receipt is consumed as a terminal no-dispatch authority for each controlled manifest; no calibration result can substitute for authorization."
  - "GB46 and BB72 retain distinct code identities, manifests, requested budgets, qualification facts, output roots, and receipt digests."
  - "Plan 11-14 may receive only receipt-declared complete pairs; the current zero-dispatch closures declare none."
patterns-established:
  - "Controlled evaluation receipts recompute canonical digests and fail closed if package, manifest, code, or receipt identity drifts."
  - "Two-code verification requires exact terminal coverage and emits an empty assessment ledger for a denied campaign."
requirements-completed: [QEV-02]
actuals:
  tokens: 8176
  tasks: 3
  commits: 5
commits: 5
plan_head_before: 7a115e92a2177186a4c1e68d72409ccd50768d0e
coverage:
  - id: D1
    description: GB46 consumes the sealed authorization as a digest-bound zero-dispatch closure with no attempted or complete evaluation pairs.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_controlled_evaluation.py::test_gb46_deny_tracer_writes_digest_bound_zero_dispatch_receipt
        status: pass
    human_judgment: false
  - id: D2
    description: BB72 preserves its provenance qualification and independent requested budget while rejecting cross-code receipt substitution.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_controlled_evaluation.py::test_bb72_cross_code_denial_retains_qualified_artifact_caveats_and_its_own_output
        status: pass
    human_judgment: false
  - id: D3
    description: The independent verifier covers both controlled manifests and exposes no assessment-ready calibration or controlled-pair ledger entries.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_controlled_evaluation.py::test_verify_all_requires_exact_terminal_coverage_and_exposes_no_calibration_evidence
        status: pass
    human_judgment: true
    rationale: "QEV-02 retains a plan-declared final manual review of authorization closure and complete-pair assessment semantics."
metrics:
  duration: 29m
  completed: 2026-10-14
status: complete
---

# Phase 11 Plan 15: Controlled Evaluation Authorization Consumer Summary

**GB46 and BB72 sealed-denial consumers emit independent digest-bound zero-dispatch receipts, and a two-code verifier admits no calibration or controlled pairs to assessment.**

## Accomplishments

- Added a fail-closed controlled-evaluation boundary that validates the sealed authorization package, frozen design, artifact/provenance identity, and code-specific campaign row before creating terminal evidence.
- Created GB46 and BB72 `denied` receipts: each contains zero scheduler submissions, attempted pairs, complete pairs, typed work, and assessment-ready ledger references.
- Added an independent verification receipt that covers both required controlled manifests, retains calibration only as forecast provenance, and reports zero assessment-ready pairs by code.

## TDD Evidence

- Task 1 RED: `7c104c1` recorded missing controlled-evaluation imports before the GB46 deny-closure implementation in `b45e8eb`.
- Task 2 RED: the BB72 focused regression failed until the receipt bound its own requested pair budget and manifest identity; the completion is in `bc93a13`.
- Task 3 RED: the verifier persistence regression failed until the verification receipt writer was added in `dfb2998`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'gb46 and (tracer or allow or deny or ineligible or blocked_precision or stale or accounting or budget or interruption)' -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'bb72 and (allow or close or provenance or precision or budget or complete_pair or interruption or cross_code)' -x` — passed (1 test).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'verify_all or terminal_coverage or receipt_digest or attempted_work or complete_pair or exceeded_budget or calibration_scope or tamper' -x` — passed (1 test).
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase11_controlled_evaluation.py verify --code gb46`, `verify --code bb72`, and `verify-all` — passed; each current authorization path remains `denied` and zero-dispatch.

## Task Commits

1. **Task 1: Consume the exact GB46 authorization through one terminal controlled path** — `7c104c1` (test), `b45e8eb` (feat)
2. **Task 2: Execute or explicitly close the exact BB72 controlled manifest** — `bc93a13` (feat)
3. **Task 3: Verify two-code receipt completeness and publication-evidence boundaries** — `dfb2998` (feat), `9913d55` (test)

## Files Created

- `src/bp_registry/campaigns/controlled_evaluation.py` — strict receipt construction, validation, and two-code verification.
- `scripts/run_phase11_controlled_evaluation.py` — preflight, zero-dispatch closure, resume, receipt verification, and two-code verification commands.
- `data/results/phase11-controlled-evaluation/gb46/evaluation-receipt.json` — GB46 sealed denial closure.
- `data/results/phase11-controlled-evaluation/bb72/evaluation-receipt.json` — BB72 sealed denial closure with artifact qualifications.
- `data/results/phase11-controlled-evaluation/verification.json` — sealed two-code terminal coverage and empty assessment ledger.
- `tests/test_phase11_controlled_evaluation.py` — denial, forged allow, stale manifest, cross-code, and calibration-scope regressions.

## Decisions Made

- Preserve the owner-reviewed denial as the only operative authority: no scheduler client is called and no dispatch capability is inferred from a calibration, proposal, or CLI route.
- Keep the current closure schema deliberately fail closed for a hypothetical allow until a qualified dispatcher can retain bounded execution, complete-pair, scheduler, interruption, and resource evidence.

## Deviations from Plan

None - plan executed exactly as written for the preserved-deny authorization state.

## Known Stubs

None. `null` resource envelope fields state that no dispatch was approved; they do not provide application data or evidence for assessment.

## Next Phase Readiness

Plan 11-14 can consume `verification.json` as exact two-code closure evidence. It must retain the result as a zero-dispatch controlled-evaluation closure: no calibration statistics or pairs are assessment inputs.

## Self-Check: PASSED

- Found all six controlled-evaluation implementation, receipt, and test files.
- Found task commits `7c104c1`, `b45e8eb`, `bc93a13`, `dfb2998`, and `9913d55`.

---
*Phase: 11-quaternary-reproduction-and-comparisons*
*Completed: 2026-10-14*
