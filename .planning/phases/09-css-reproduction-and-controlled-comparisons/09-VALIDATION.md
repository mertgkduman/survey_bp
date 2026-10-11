---
phase: "09"
slug: "css-reproduction-and-controlled-comparisons"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-11"
---

# Phase 9 — Validation Strategy

> Initial strategy from `09-RESEARCH.md`; the planner must replace the provisional task map with exact plan/task IDs and executable commands.

## Test Infrastructure

| Property | Value |
| --- | --- |
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <focused phase-9 test files> -x` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure on first Phase 9 run; no unmeasured ceiling assumed |

## Sampling Rate

- **After every task commit:** Run the focused test file for the changed source, statistics, voting, or campaign contract.
- **After every plan wave:** Run the full suite and record elapsed time, peak memory, and exit status.
- **Before `$gsd-verify-work`:** Run the full suite and independently reconstruct retained source, tracer, voting, paired, and production-authorization receipts.
- **Max feedback latency:** Determine from the first measured focused/full runs; do not invent a bound.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | EVAL-01 | Source substitution | Pinned identities, typed unavailable native status, no false faithful label | unit/integration | Focused source qualification tests | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | EVAL-02 | Target/denominator drift | Failure-count exact inference, caps, censoring, target provenance | unit/property/integration | Focused campaign target and statistics tests | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | EVAL-03 | Pair or cost substitution | Matched sample identity and complete work/resource accounting | integration | Focused campaign execution/report tests | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CAN-02 | Invalid ballots or hidden truth | Public vote execution, original-syndrome check, full replay | unit/integration | Focused voting and public CLI tests | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

## Wave 0 Requirements

- [ ] Source/target/native-status fixtures for all three selected paper revisions.
- [ ] Failure-count stopping and inverse-binomial interval fixtures, including cap censoring and coverage boundaries.
- [ ] Asymmetric acceptance-rule fixtures that keep source uncertainty distinct from the prespecified tolerance.
- [ ] Public voting fixtures for ties, abstentions, exclusions, invalid aggregate, empty eligible set, replay, and worker-order independence.
- [ ] A bounded Yao B1 `T=1` adaptation tracer and resource-measurement receipt.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
| --- | --- | --- | --- |
| Source-authored numeric target or digitization audit | EVAL-01, EVAL-02 | Requires inspection of the pinned source figure or author data | Compare literal points, locator, source digest, rounding/digitization interval, and extraction receipt before freezing assessment. |
| Publication-scale site authorization | EVAL-03 | Site ceilings and allocation accounting have not been observed | Inspect measured wall, cores, memory, storage, scheduler policy, and the profiling gate; retain denial until the receipt is complete. |

## Validation Sign-Off

- [ ] Every task has an executable `<automated>` check or a Wave 0 dependency.
- [ ] No three consecutive tasks lack an automated check.
- [ ] Wave 0 covers every missing fixture named above.
- [ ] No watch-mode flags.
- [ ] Focused feedback latency measured.
- [ ] `nyquist_compliant: true` set only after independent verification.

**Approval:** pending plan verification
