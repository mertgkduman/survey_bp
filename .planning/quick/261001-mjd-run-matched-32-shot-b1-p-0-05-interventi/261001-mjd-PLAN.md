---
phase: quick
plan: 261001-mjd
status: ready
created: 2026-10-01
---

# Matched low-noise intervention and damping pilot

Run a new B1 CSS mechanism pilot at physical error rate 0.05 on 128 matched
physical samples. Pair the existing seven single-intervention arms with seven
otherwise identical V2C damping arms at the explicit Phase 4 fresh-message
coefficient gamma=0.5. This is a controlled composition pilot, not source-curve
reproduction or a decoder ranking. The user selected the count and coefficient.

## Task 1: Admit and execute the composition

Extend the versioned public and compact manifest contracts without changing V5/V6
meaning. Make damping available to every Phase 5 BP session, including independent
shortened attempts and restart residual solves. Preserve per-attempt reset,
reserve-before-compute, original-problem validation, typed work, and replay.
Reject unsupported memory and intervention combinations before sampling.

## Task 2: Verify semantics

Add independent small-code tests for the gamma equation and history reset; test
all seven arms through public preflight, execution, and replay with damping on
and off. Check that gamma=1 matches undamped behavior and that denied work does
not advance damping history.

## Task 3: Freeze and run the new design

Write a separate machine-readable design with new physical and decoder seed
namespaces, p=0.05, 128 matched sample IDs, 14 manifest identities, source
qualification, finite caps, and an explicit stop rule. Check HPC entitlement
and a small objective calibration before sealing it. Execute within that seal
and retain all terminal, attempt, candidate, work, and run evidence. Avoid
reusing or modifying the p=0.07 pilot.

## Task 4: Report and track

Produce a concise read-only comparison of valid, unavailable, and logical
outcomes plus work and limits, with no superiority claim. Verify aggregate
sample matching, ledger digests, and every arm replay. Commit the intended
code, tests, manifest, results, and quick summary; update STATE.md. Do not
stage unrelated untracked files.
