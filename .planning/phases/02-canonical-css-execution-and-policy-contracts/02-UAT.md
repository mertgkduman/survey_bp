---
status: complete
phase: 02-canonical-css-execution-and-policy-contracts
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
  - 02-05-SUMMARY.md
  - 02-06-SUMMARY.md
  - 02-07-SUMMARY.md
  - 02-08-SUMMARY.md
  - 02-09-SUMMARY.md
started: 2026-09-23T16:02:31Z
updated: 2026-09-23T17:11:04Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-End Canonical CSS Run
expected: Running the documented canonical three-qubit manifest through the public CLI completes successfully, writes a result plus version-two structural ledger evidence, and reports an independently evaluated decoder outcome without exposing hidden truth to decoder policies.
result: pass

### 2. Seven-Role Policy Composition Inspection
expected: Inspecting the canonical manifest and preflight output shows all seven explicit policy roles resolved through the closed registry with deterministic identities, declared lifetimes, ownership, capabilities, and procedure evidence; invalid or hidden-truth-reaching compositions are rejected.
result: pass

### 3. Candidate Lineage and Trace Inspection
expected: Inspecting a canonical result shows stable typed lineage for generated, validated, selected, and evaluated candidates; the selected payload remains available, structural events are queryable, and any optional semantic trace is hash-linked, confined, and explicitly truncated when capped.
result: pass

### 4. Budget and Termination Semantics
expected: A researcher can distinguish hierarchical scopes, reserve-before-work count limits, wall-clock boundary checks, rollback behavior, and the recorded termination reason without mistaking a partial sweep for committed work.
result: pass

### 5. Tutorial and Mathematical Contract Readability
expected: Following docs/canonical-engine.md from a clean output directory is sufficient to run, verify, inspect, and reconcile the canonical example, while the mathematical conventions and lifecycle boundaries are understandable without reading implementation internals.
result: pass

### 6. Profiling, Tracing, and Novelty Boundaries
expected: The profiling/tracing strategy and novelty register clearly distinguish representative from diagnostic evidence, preserve missingness and replay limitations, and avoid presenting provisional diagnostics or implementation depth as validated population or novelty claims.
result: pass

### 7. Named Finite Numerical Profile and Tie Semantics
expected: Named finite numerical profile, LLR encoding, degree-one check rule, and deterministic tie handling.
result: pass
source: automated
coverage_id: D1-02-03

### 8. Canonical Flooding Sweep Semantics
expected: Canonical edge ordering and complete old/new-buffer flooding sweep semantics with proposed work counts.
result: pass
source: automated
coverage_id: D2-02-03

### 9. Lineage-Derived Work Accounting
expected: Unique leaf work vectors reduce through branch, leg, member, search, and shot ancestry without double counting; iteration and resource facts remain qualified.
result: pass
source: automated
coverage_id: D2-02-04

### 10. Native Metric Observability
expected: Native adapter exposes qualified observed iteration facts and explicit unavailable opaque internal counters.
result: pass
source: automated
coverage_id: D1-02-06

### 11. Missingness-Preserving Native Evidence
expected: Terminal, reconciliation, summary, and result paths preserve typed missingness without coercing unavailable work to zero.
result: pass
source: automated
coverage_id: D2-02-06

### 12. Local Profiling Behavior
expected: Default-on local timing, CPU, RSS, allocation, allowlisted-context, disabled, unavailable, and strict-required profiling behavior.
result: pass
source: automated
coverage_id: D1-02-07

### 13. Paired Profiling Replay Evidence
expected: Prespecified representative and diagnostic cohort claims, paired replay provenance, semantic agreement, divergence retention, and timing-independent trace digest.
result: pass
source: automated
coverage_id: D2-02-07

### 14. Strict Canonical Manifest Preflight
expected: Strict canonical manifest schema and immutable preflight.
result: pass
source: automated
coverage_id: D1-02-08

### 15. Public Canonical Structural Evidence
expected: Public canonical execution with structural terminal evidence and independently evaluated outcomes.
result: pass
source: automated
coverage_id: D2-02-08

## Summary

total: 15
passed: 15
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]

## Completion Blockers

- type: commit_claim_mismatch
  summary: 02-01-SUMMARY.md
  claimed: 2
  measured_from_plan_head_to_current_head: 50
- type: commit_claim_mismatch
  summary: 02-02-SUMMARY.md
  claimed: 4
  measured_from_plan_head_to_current_head: 47
- type: commit_claim_mismatch
  summary: 02-03-SUMMARY.md
  claimed: 4
  measured_from_plan_head_to_current_head: 42
- type: commit_claim_mismatch
  summary: 02-04-SUMMARY.md
  claimed: 5
  measured_from_plan_head_to_current_head: 30
- type: commit_claim_mismatch
  summary: 02-05-SUMMARY.md
  claimed: 5
  measured_from_plan_head_to_current_head: 36
- type: commit_claim_mismatch
  summary: 02-06-SUMMARY.md
  claimed: 4
  measured_from_plan_head_to_current_head: 24
- type: commit_claim_mismatch
  summary: 02-07-SUMMARY.md
  claimed: 4
  measured_from_plan_head_to_current_head: 19
- type: commit_claim_mismatch
  summary: 02-08-SUMMARY.md
  claimed: 6
  measured_from_plan_head_to_current_head: 14
- type: commit_claim_mismatch
  summary: 02-09-SUMMARY.md
  claimed: 4
  measured_from_plan_head_to_current_head: 6
