---
phase: 04-memory-policies-and-relay-bp
reviewed_commit: 6747e90bf02a1072e17a6c106bc2cc3ab937d1a8
reviewed: 2026-09-27T18:45:25Z
rechecked: 2026-09-27T18:50:19Z
correction_commit: a44f270
scope: surface_integrity_only
files_reviewed:
  - scripts/verify_phase4_calibration.py
  - tests/canonical/test_phase4_calibration_verification.py
producer_compared: scripts/run_phase4_pilots.py
status: findings_resolved_after_bounded_recheck
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 3
  warning: 0
  info: 0
---

# Phase 04 calibration surface audit review

This is a bounded review of commit `6747e90`'s terminal calibration surface
audit. It does not inspect live or partial calibration outcomes, replay a
ledger, select settings, or give a Phase 04 verdict. The findings preserve the
audit's `surface_integrity_only` boundary: they concern planned sample identity,
aggregate accounting, and terminal-status reconstruction.

## Critical Issues

### CR-01: Arbitrary and reused samples can pass as matched calibration evidence

**Files:** `scripts/verify_phase4_calibration.py:114-120`, `src/bp_registry/sampling.py:111-113`

**Issue:** The audit only requires a nonempty `sample_identity` and equality
between configurations with the same `(code_id, shot_id)`. It neither derives
the expected frozen calibration identity nor rejects the same identity at
different shot IDs. The sampling contract makes identities a hash of the
physical sample namespace and shot ID. Consequently, a result in which every
terminal row uses one arbitrary identity, or an identity from the evaluation
namespace, passes the audit as a complete matched calibration. Its repeated
outcomes are then counted as independent shots for the Wilson interval and can
determine `selected-settings.json`.

I reproduced this with the submitted test surface by changing every completed
attempt's identity to `reused-sample`; `audit_surface()` still returned
`status: passed` with two eligible configurations and four retained attempts.

**Fix:** For each terminal attempt, materialize the frozen calibration manifest
for its cell and derive the public shot context for its `shot_id`; require
`attempt["sample_identity"]` to equal that context's deterministic sample
identity. Also maintain a per-code set of identities and reject an identity
claimed by more than one shot ID. This validates the frozen namespace and
independence-facing identity at the surface boundary; canonical ledger replay
can remain a separate gate.

Add regressions that (a) replace all shot identities with one value, and (b)
substitute a deterministic evaluation-namespace identity while preserving
cross-preset equality.

### CR-02: Re-entering a cap-reached run rewrites its terminal status and then fails the audit

**Files:** `scripts/run_phase4_pilots.py:949`, `scripts/run_phase4_pilots.py:1027-1030`, `scripts/verify_phase4_calibration.py:145-148`

**Issue:** `run_calibration()` initializes `cap_reached` to `False` on every
call. A second call over a retained terminal result has no unretained shots, so
it never sets the local flag even when the rows still contain `status ==
"cap_reached"`. It rewrites the valid terminal status to
`completed_with_inconclusive`. The submitted audit correctly reconstructs
`cap_reached` from those retained rows and rejects the producer's rewritten
result. This makes a valid capped run unauditable after the documented
run-or-resume function is invoked again.

An isolated fixture with a cap below one public boundary produced
`cap_reached` on the first invocation, `completed_with_inconclusive` on the
second, and `ValueError: terminal aggregate status does not reconstruct` from
`audit_terminal()`.

**Fix:** Treat retained cap placeholders as authoritative when resuming, e.g.
initialize `cap_reached` from every existing attempt status before traversing
cells, or return an already terminal, digest-valid result without rewriting it.
Add a producer/audit regression for a cap-reached result passed to
`run_calibration()` twice.

### CR-03: Reconciliation double-counts a previously charged interrupted attempt

**Files:** `scripts/run_phase4_pilots.py:944-948`, `scripts/run_phase4_pilots.py:974-981`, `scripts/verify_phase4_calibration.py:142`

**Issue:** An `incomplete_public_boundary` row can already carry its measured
`category_charge_seconds` when canonical execution reached a terminal but the
mandatory verification call failed or timed out. On resume, `used_wall` starts
by including that old charge. Reconciliation replaces the row's charge with
the declared boundary and then adds the whole new boundary to `used_wall`
without removing the old one. The saved allocation is therefore
`old_elapsed + declared_boundary`, whereas the audit reconstructs the retained
row as only `declared_boundary` and rejects it. The recovery path intended to
retain a verified terminal without rerunning the public command cannot pass the
new calibration gate.

**Fix:** Capture the old charge before reconciliation and update the running
total by `new_charge - old_charge`, or recompute the retained charge after each
attempt mutation. Add a test for a terminal with a failed/timeout verification
that is successfully reconciled on the next invocation, then require
`audit_terminal()` to pass.

## Verification

- `OMP_NUM_THREADS=1 /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q tests/canonical/test_phase4_calibration_verification.py` — 16 passed.
- A read-only synthetic identity substitution demonstrated CR-01; an isolated
  temporary cap fixture demonstrated CR-02. No production calibration receipt,
  event ledger, partial outcome, selection, or evaluation artifact was read.

## Bounded correction recheck

All three reported findings are resolved by correction commit `a44f270`.
This is a correction-only recheck, not a Phase 04 verdict.

- **CR-01 resolved:** `audit_surface()` now reconstructs the sample identity
  from the frozen calibration namespace and `shot_id`, matching the public
  sampler's documented hash. The added regressions reject both reused
  cross-shot identities and evaluation-namespace substitutions while retaining
  the separate ledger-replay boundary.
- **CR-02 resolved:** `run_calibration()` preserves a terminal result after
  checking its exact plan, cap bytes, amendment, and self-digest. For a running
  resume, retained cap placeholders also seed the terminal-status calculation.
  The new twice-invoked capped fixture preserves `cap_reached` and passes the
  surface audit both times.
- **CR-03 resolved:** Reconciliation now adjusts retained wall accounting by
  `new_charge - prior_charge`, so the allocation remains equal to the charges
  reconstructed from retained attempts.

The focused calibration audit suite passed: **21 passed**. No source was
modified by this recheck, and no live calibration result or ledger was read.
