---
phase: 04-memory-policies-and-relay-bp
plan: "08"
subsystem: native-relay-qualification
tags: [relay-bp, provenance, native, observer]
requires: [04-07]
provides: [pinned-relay-v022-adapter, relay-observer-boundary]
affects: [MOD-01]
tech-stack:
  added: [Rust Cargo workspace qualification]
  patterns: [strict decoder-visible translation, pinned-source provenance]
key-files:
  created:
    - src/bp_registry/native/relay_v022.py
    - scripts/qualify_relay_v022.py
    - native/relay-v0.2.2-observer.patch
    - data/evidence/relay-v0.2.2-source.json
  modified:
    - tests/canonical/test_relay_differential.py
decisions:
  - "The adapter never imports relay_bp by name; its runner is injected from the isolated exact-author build."
  - "The observer is comment-only, so gamma, edge-work, and resource facts remain unavailable."
metrics:
  duration: "~25m"
  completed: "2026-09-24"
status: complete
plan_head_before: 2ee1a05d15dd681472f42fec2e4abc5f69a471f5
commits: 5
actuals:
  tokens: 26160
  tasks: 2
  commits: 5
---

# Phase 04 Plan 08: Pinned Relay v0.2.2 Native Qualification Summary

Built an isolated, exact-author Relay v0.2.2 qualification envelope with a behavior-neutral observer boundary.

## Accomplishments

- Added `RelayV022Adapter`, which accepts only a binary check matrix, syndrome, error priors, approved Relay settings, seed, and an explicit `f32` or `f64` profile. It rejects hidden truth and cannot import the installed fork accidentally.
- Added an exact-pin qualification script and source record. The record binds `trmue/relay` tag `v0.2.2` to commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3` and tree `5f6f112429e62112ba71fbff45f4e16247725fbc`, while preserving distinct moving-main and installed-fork identities.
- Added a git-applicable observer patch based on the exact commit. It is comment-only, then tested by rebuilding all native test targets and executing deterministic Relay repetition and bounded 72-by-144 BB-144 CSS fixtures before and after the patch.
- Added nine differential contracts for source identity, decoder-visible translation, explicit precision, patch identity, terminal fields, bounded BB-144 evidence, and unavailable facts.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay_differential.py -k 'source_identity or translation or unmodified or numerical_profile'` — 5 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay_differential.py -k 'observer or equivalence or bb144 or unavailable'` — 3 passed.
- `scripts/qualify_relay_v022.py` — all workspace test targets built; the bounded `min_sum_decode_repetition_code` Relay fixture passed unmodified and patched.
- The exact-author Python bindings ran the selected CSS gross-BB-144 72-by-144 fixture with `pre_iter=1`, `num_sets=1`, `set_max_iter=1`, seed 19, and a 60-second timeout. Candidate and posterior digests, success, and aggregate iterations agree field by field; native score and log stream are explicitly unavailable.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 3 - Blocking build issue] v0.2.2's committed Cargo lock required normalization on this host and the required crates were not cached.
   - **Found during:** Task 1
   - **Fix:** Used Cargo's declared manifest dependencies in an isolated exact-pin checkout; the author commit and tree remained fixed.
   - **Files modified:** `scripts/qualify_relay_v022.py`, `data/evidence/relay-v0.2.2-source.json`
   - **Commit:** c55be03

2. [Rule 1 - Bounded-suite handling] The author `decode_144_12_12` native test was CPU-bound for more than 720 seconds.
   - **Found during:** Task 1
   - **Fix:** Built every workspace test target and ran the small deterministic Relay fixture under a 120-second bound. The full-case result is recorded as `inconclusive_timeout`, not a pass.
   - **Files modified:** `scripts/qualify_relay_v022.py`, `data/evidence/relay-v0.2.2-source.json`
   - **Commit:** c55be03

## Known Limits

- The full author `decode_144_12_12` test remains inconclusive after its 720-second bound; this does not invalidate the separately bounded 72-by-144 terminal comparison.
- The comment-only observer cannot expose per-leg gamma, edge work, or resource metrics without changing decoder behavior. The source record retains all three as unavailable.

## Self-Check: PASSED

- Confirmed all five plan artifacts exist.
- Confirmed task commits `36bb46e`, `c55be03`, and `a272b2d` exist.
