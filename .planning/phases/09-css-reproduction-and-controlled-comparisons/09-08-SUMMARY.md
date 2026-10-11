---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "08"
subsystem: canonical-mbbp-vote-policy
tags: [css, mbbp, vote, public-replay, provenance]
requires:
  - phase: 09-css-reproduction-and-controlled-comparisons
    plan: "07"
    provides: public MBBP vote decision and event projection
provides:
  - public V7 vote terminal and semantic replay
  - closed Rabeti coordinate-majority vote policy
  - caller-owned vote gate command
affects: [CAN-02, EVAL-01]
tech-stack:
  added: []
  patterns: [manifest-tie-bit-passthrough, semantic-ledger-replay, closed-policy-vote-controls]
key-files:
  created:
    - literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld-vote.toml
  modified:
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/ledger.py
    - src/bp_registry/literature.py
    - scripts/run_css_literature_gate.py
    - tests/test_canonical_cli.py
    - tests/test_literature_policy.py
    - tests/test_css_literature_gate.py
key-decisions:
  - "V7 execution and independent replay pass the persisted manifest tie bit to the closed vote projection."
  - "Vote candidate validation, evaluation, and terminal status derive from the vote projection rather than the list-selection result."
  - "The Rabeti vote TOML is a canonical_adaptation_not_assessed mechanism policy; source partition, artifact, and native implementation blockers remain unresolved."
  - "The public vote gate writes only to the caller-selected cache root and verifies the complete terminal evidence before returning."
actuals:
  tokens: 5812
  tasks: 2
  commits: 2
plan_head_before: 571d423a01e88bb6883bf455a9fab9b74151acb1
duration: 32m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 08: Public MBBP Vote Policy Summary

Public coordinate-majority voting now executes and independently replays through the canonical V7 ledger, and a distinct Rabeti policy file exposes the mechanism as a labeled canonical adaptation.

## Accomplishments

- Added the five explicit vote event kinds to the V7 ledger grammar.
- Passed `parsed.vote.tie_bit` into both execution and verification, with no implicit default.
- Corrected V7 vote execution to validate, evaluate, and terminalize the projected vote candidate instead of the list-selection candidate.
- Added rehashed-ledger tamper coverage for electorate, tie bit, ballots, aggregate, lineage, original validity, and work.
- Added `mbbp-ld-vote.toml`, with a closed correction-bit/admitted-member/coordinate-majority/tie-bit declaration distinct from the list policy.
- Extended the closed literature parser to accept only the exact declared Rabeti vote controls and reject incomplete or unknown vote fields.
- Added `scripts/run_css_literature_gate.py vote` to compile, execute, cache, and independently replay the vote policy in caller-owned output.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py -k 'vote and (run or verify or tamper or replay)' -x` — 1 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py tests/canonical/test_mbbp.py tests/canonical/test_voting.py -k 'vote or list_regression or no_member' -x` — 11 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_css_literature_gate.py -k 'vote or policy_file or replay or cache or adaptation' -x` — 4 passed, 26 deselected in 128.22s.
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_css_literature_gate.py vote --study data/studies/css-literature-b1-gate-v1.json --output /tmp/phase09-vote-gate.ehDky7` — verified two bounded B1 terminal rows; cache key `6fcf169f5625738a47fd58a7a0b849cc37821c9610163ca6757bcfeb961dd9d8`.

## Task Commits

1. **Task 1: Run and independently replay one public voting ledger**
   - `d7ae1dc` `feat(09-08): replay public MBBP vote terminals`
2. **Task 2: Compile and execute voting from a public literature policy file**
   - `4ed9d91` `feat(09-08): add public Rabeti vote policy`

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 2 - Missing critical functionality] Added the vote event kinds to the V7 ledger allowlist.**
   - **Found during:** Task 1 public execution.
   - **Issue:** Phase 07 projected the complete vote evidence, but `CanonicalEventWriter` rejected each vote event before a public terminal could be written.
   - **Fix:** Added the five existing Phase 07 vote event names to the additive V7 canonical ledger grammar while preserving every prior event name and version.
   - **Files modified:** `src/bp_registry/ledger.py`.
   - **Commit:** `d7ae1dc`.

2. **[Rule 1 - Bug] Replayed the vote terminal rather than the underlying list terminal.**
   - **Found during:** Task 1 public replay.
   - **Issue:** The existing V7 boundary discarded the manifest tie bit and used the list-selected candidate and terminal after building a vote projection.
   - **Fix:** Passed the tie bit to both paths and used the projection candidate and terminal status for original-syndrome validation, outcome evaluation, and replay equality.
   - **Files modified:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`.
   - **Commit:** `d7ae1dc`.

## Known Stubs

None.

## Self-Check: PASSED

- Found the vote policy, vote gate, execution/replay wiring, ledger grammar, and focused tests.
- Found task commits `d7ae1dc` and `4ed9d91` in repository history.
