---
phase: 02-canonical-css-execution-and-policy-contracts
verified: 2026-09-23T21:23:56Z
status: gaps_found
score: 2/5 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/phases/02-canonical-css-execution-and-policy-contracts/02-REVIEW.md
  - .planning/phases/02-canonical-css-execution-and-policy-contracts/02-UAT.md
  - docs/canonical-engine.md
  - src/bp_registry/canonical/budgets.py
  - src/bp_registry/canonical/contracts.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/kernel.py
  - src/bp_registry/canonical/lineage.py
  - src/bp_registry/canonical/problems.py
  - src/bp_registry/canonical/profiling.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - tests/test_canonical_cli.py
covered_digest: "v1:sha256:143ca72c525f06fe6580a18e43b6c5790425ac693a082a41157eb19c1b6941e7"
behavior_unverified: 0
---

# Phase 2: Canonical CSS Execution and Policy Contracts Verification

**Phase goal:** A researcher can inspect and run a canonical binary BP policy composition and trust its outcomes and computational attribution.

**Verdict:** Gaps found. The complete test suite passes (`126 passed` on 2026-09-23), and the basic canonical run exists. The public path does not yet honor its advertised policy composition or resource limits, and its checked ledger falsely records zero BP calls. The prior 15/15 UAT result is therefore not evidence that the phase goal is achieved. Its incorrect per-plan commit counts were audited separately and are no longer a blocker.

## Goal achievement

| Roadmap success criterion | Verdict | Evidence |
| --- | --- | --- |
| 1. CSS manifest runs project-owned BP through independent evaluation and a ledger | Verified | Public canonical fixture and CLI tests execute the project-owned `BinarySpaKernel` and evaluate a recovery. |
| 2. Typed policy lifecycle, compatibility, truth isolation, and scoped stopping are enforced at execution | Failed | Composition is validated, then only `traverse_lifecycle()` runs; `BinarySpaKernel` executes fixed behavior. Public work limits are discarded before execution. See CR-01, CR-02. |
| 3. Deterministic small cases verify numerics and policy-contract invariants | Verified | Canonical numerical, flooding, contract, and truth-boundary unit tests pass; these do not establish public dispatch. |
| 4. Queryable control-flow and honest work/runtime attribution | Failed | Every checked attempt invokes BP but records `bp_calls: 0`; a non-owner can inject structural events. See CR-03, CR-04. |
| 5. Runnable tutorial with correct mathematical and compatibility conventions | Failed | Tutorial run works, but its syndrome equation names `Hx` where implementation uses `Hz` for X-error recovery. See WR-04. |

## Requirement disposition

| Requirement | Verdict | Reason |
| --- | --- | --- |
| ENG-01 | Satisfied for fixed binary SPA | Public manifest reaches project-owned kernel, evaluator, and ledger. |
| ENG-02 | Blocked | Accepted role bindings are not dispatched into the kernel. |
| ENG-03 | Blocked | Scoped manifest work limits are not enforced on the public path. |
| ENG-04 | Partial | Kernel conventions are tested, but the tutorial states the wrong check-matrix equation. |
| ENG-05 | Partial | Truth is isolated, but selection may attach a candidate from unrelated working lineage. |
| ENG-06 | Partial | Baseline equations/invariants exist; accepted policy names are not executed. |
| SCH-01 | Partial | Flooding semantics are tested in isolation; public policy dispatch is fixed. |
| LED-02 | Blocked | Structural records admit non-owner injection and enabled tracing is ignored. |
| LED-03 | Blocked | BP-call attribution is false and resource caps are not applied. |
| LED-04 | Satisfied | Native missingness is explicit in current tests. |
| DOC-01 | Partial | Tutorial executes but contains a reversed syndrome convention. |

## Critical gaps for closure plans

1. **CR-01 — policy dispatch:** Resolve supported role bindings to engine-owned implementations and execute at their declared hooks. Reject every unsupported non-baseline binding at preflight rather than label a fixed run with a false policy identity. Integration tests must show that every accepted binding affects declared behavior/evidence or is explicitly identity-only.
2. **CR-02 — scoped budgets:** Preserve manifest caps, define work-resource units, and reserve the complete operation before mutation. On denial, emit the correct scope/reason with no committed sweep work. Cover public CLI and a cap below one sweep.
3. **CR-03 — BP-call accounting:** Include one `bp_calls` unit for each actual kernel invocation in both reservation and terminal evidence; verify checked and freshly generated ledgers.
4. **CR-04 — shot ownership:** Require the active shot owner for every intermediate append, reject lifecycle kinds through `event()`, and test a second writer/process attempting injection.

## Other review gaps to resolve before passing

- WR-01: `LocalProfiler.measure()` must stop its own `tracemalloc` on action exceptions.
- WR-02: `ReplayLink` must bind its cohort to the correct sample/run identity before population claims.
- WR-03: Public trace/profile plans must be honored observationally, or unsupported enabled plans rejected at preflight.
- WR-04: Correct `s_Z = H_Z e_X (mod 2)` tutorial convention and its anchor test.
- WR-05: Reject fractional, string, boolean, and non-vector candidate payloads before content-addressing.
- WR-06: Verify working-problem parent edge and selected candidate lineage against the current original and attempt.
- WR-07: Remove canonical-path import-time dependency on native `ldpc` and test without it.

## Reverification criteria

Run the full test suite, a fresh documented canonical CLI run and ledger verification, adversarial ownership/lineage tests, and a public cap-denial test. Recheck every review finding against source and evidence, then rerun code review and security/verification gates. Do not close Phase 2 on the current UAT pass alone.
