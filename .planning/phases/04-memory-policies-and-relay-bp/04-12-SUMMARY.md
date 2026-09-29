---
phase: 04-memory-policies-and-relay-bp
plan: "12"
subsystem: finite Relay memory calibration evidence
tags: [relay-bp, calibration, ledger-audit, selection, provenance]
requires:
  - phase: 04-11
    provides: frozen one-worker caps, disjoint sample namespaces, and a bounded calibration plan
provides:
  - Terminal three-code, two-preset calibration surface with complete Relay-ledger verification
  - Digest-bound deterministic per-preset and shared-memory selections
  - Explicit B1 inconclusive outcome under the frozen cap
affects: [04-13, 04-14, relay-evaluation, phase-4-verification]
tech-stack:
  added: []
  patterns: [terminal-only streaming ledger reconstruction, calibration-only deterministic selection]
key-files:
  created: [.planning/phases/04-memory-policies-and-relay-bp/04-12-SUMMARY.md]
  modified: [.planning/async-jobs/04-12-calibration-v4-active.json]
decisions:
  - "Treat B1 as inconclusive because neither preset has an eligible complete configuration under the frozen cap."
  - "Reconcile the async manifest from terminal result and independent ledger evidence without rerunning or rewriting retained result files."
requirements-completed: [MOD-01, MEM-04, MEM-05]
actuals:
  tokens: 75491
  tasks: 2
  commits: 84
plan_head_before: fb2414b3bc613ba349a949084ca4deb5d47bee71
metrics:
  duration: "2026-09-25 to 2026-09-29 terminal reconciliation"
  completed: 2026-09-29
status: complete
coverage:
  - id: D1
    description: Complete frozen calibration surface and every retained terminal are independently reconstructed from manifests and Relay ledgers.
    requirement: MEM-04
    verification:
      - kind: integration
        ref: "scripts/verify_phase4_calibration.py --root . --ledgers"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_phase4_calibration_ledgers.py"
        status: pass
    human_judgment: false
  - id: D2
    description: Per-preset and shared settings are derived only from terminal calibration evidence, retaining inconclusive B1 entries.
    requirement: MOD-01
    verification:
      - kind: unit
        ref: "tests/canonical/test_phase4_evidence.py -k 'selection_rule or tie_break or shared_settings or insufficient_precision'"
        status: pass
      - kind: other
        ref: "read-only byte-for-byte reconstruction with select_calibration_settings"
        status: pass
    human_judgment: false
---

# Phase 04 Plan 12: Finite Relay Calibration and Selection Summary

Terminal calibration retained all 5,824 planned attempts, passed independent Relay-ledger reconstruction, and froze calibration-only settings while keeping B1 explicitly inconclusive.

## Performance

- **Campaign and reconciliation:** 2026-09-25 to 2026-09-29
- **Tasks:** 2/2 complete
- **Tracked closeout files:** 2
- **Retained calibration result:** 97,183,929 bytes, SHA-256 `59a5f27fc8271724f603741c4311becfaca52a7ef01bbb93d240a823f58f2fef`

## Accomplishments

- Verified all 182 frozen configurations and all 5,824 retained terminal shots against their manifests, event grammar, exact per-shot ledger digests, Relay work, sample identities, outcomes, and termination facts.
- Preserved 5,371 completed and 453 budget-exhausted attempts under the frozen 688,243-second calibration cap; the result status is `completed_with_inconclusive`.
- Recomputed `selected-settings.json` byte-for-byte from calibration evidence only. BB-144 and HGP selections remain finite-precision limited; B1 source, canonical, and shared selections remain `inconclusive` because no eligible complete configuration exists under the frozen cap.
- Reconciled the stale async-job manifest to terminal evidence without relaunching the campaign or changing retained calibration/result bytes.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'calibration or coarse_grid or refinement_cap or no_leakage or retained_failure'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'selection_rule or tie_break or shared_settings or insufficient_precision'` — 2 passed.
- `OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python scripts/verify_phase4_calibration.py --root . --ledgers` — passed: 182/182 configurations, 5,824/5,824 terminal shots; aggregate ledger SHA-256 `205f8fca7ff3fc00732dd68d1d697a4bac614235f4112a2b9f266158c1ad744d`.
- `OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python -m pytest -q tests/canonical/test_phase4_calibration_ledgers.py` — 1 passed.
- Read-only `select_calibration_settings(result) == selected-settings.json` reconstruction — passed; selected settings SHA-256 `079024069b6866b8a458ffeb03fe7a581ec1074ade7ff3a74e70803bb323300c`.

The first long-running terminal-ledger audit was stopped before completion because it had been started without a persistent output session and could not yield a reviewable final verdict. The persistent rerun above was read-only and produced the recorded passing result. The two `test_phase4_evidence.py` commands are separate prescribed calibration and selection gates, each run once.

## Task Commits

1. **Task 1: Execute the complete prespecified calibration search** — `f7227a3` retained resumable calibration attempts; `263501e` added the terminal Relay-ledger reconstruction; `91926c5` reconciled the async manifest from the verified terminal evidence.
2. **Task 2: Select per-preset and shared settings deterministically** — `73a7358` introduced the finite deterministic selector. The frozen selection artifact is an intentionally untracked retained result and was validated in place.

## Files Created/Modified

- `.planning/async-jobs/04-12-calibration-v4-active.json` — terminal status, exact result and aggregate-ledger hashes, coverage, selection, and B1 inconclusive evidence.
- `.planning/phases/04-memory-policies-and-relay-bp/04-12-SUMMARY.md` — completed-plan record and verification evidence.
- `data/results/phase4-memory-relay/calibration/result.json` — preserved terminal producer result; not rewritten or committed.
- `data/results/phase4-memory-relay/selected-settings.json` — preserved frozen selection artifact; not rewritten or committed.

## Decisions Made

- B1 remains inconclusive for both presets and shared settings. There is no eligible complete configuration within its frozen work cap, so a winner cannot be selected.
- The async manifest records `completed_with_inconclusive`, matching the producer result and independent ledger audit rather than treating an available result file as evidence to relaunch.
- Calibration does not use evaluation samples: all three calibration namespaces are distinct from the corresponding evaluation namespaces, and the terminal result records `evaluation_namespace_accessed: false`.

## Deviations from Plan

None - the terminal campaign completed within its prespecified cap. The delayed closeout reconciled the existing async job rather than dispatching a duplicate campaign.

## Known Limitations

- B1 has no eligible source, canonical, or shared setting under the frozen cap. Plan 04-13 must retain this outcome and cannot manufacture a B1 selected arm from this calibration.
- The retained finite samples use Wilson 95% intervals and remain finite-precision limited; they are not publication-precision performance claims.

## Next Phase Readiness

- BB-144 and HGP per-preset and shared settings are frozen for the separately gated fresh evaluation work.
- Plan 04-13 must preserve B1 as an explicit inconclusive arm until independently qualifying evidence is available.

## Self-Check: PASSED

- The summary and reconciled async manifest exist.
- Historical task commits `73a7358`, `f7227a3`, `263501e`, and reconciliation commit `91926c5` exist in repository history.

---
*Phase: 04-memory-policies-and-relay-bp*
*Completed: 2026-09-29*
