---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "09"
subsystem: campaigns
tags: [profile, yao, canonical-adaptation, local-measurement]
status: complete
dependency_graph:
  requires: [09-06]
  provides: [measured small policy tracer, replayed local resource gate]
  affects: [09-10, 09-11]
key_files:
  created: [data/manifests/phase9-yao-small-profile.json, data/studies/phase9-css-profile-tracer-v1.json, data/results/phase9-css-profile-tracer-v1/profile-gate.json, scripts/phase9_profile_gate.py, tests/test_phase9_profile_gate.py]
  modified: [src/bp_registry/campaigns/execution.py]
actuals:
  tasks: 2
  commits: 2
---

# Phase 09 Plan 09: Measured Small Yao Profile

## Delivered

- Compiled the tracked Yao `bpgd-t001` policy against the algebraic three-qubit CSS fixture and froze two preselected sample IDs, finite local caps, one worker, and a development-only target before running.
- Executed the installed public failure-count path through plan, local runs, merge, resume, assess, and verify. Fixed canonical guided-decimation event extraction so campaign receipts read the terminal and work vector from its typed nested payload. The retained two-shot cap-censored result is `development_fixture` and `not_assessed`; it carries no curve or ranking claim.
- Retained `profile-gate.json` with verified execution wall time 7,165,244,124 ns, child CPU 3,040,957,000 ns, peak child RSS 124,846,080 bytes, replay wall 3,391,209,196 ns, replay CPU 1,434,987,001 ns, decoder work 24, events 22, evidence 28,504 bytes, and storage 37,740 bytes. Site ceilings and scheduler accounting are typed unavailable, and publication Slurm is denied.
- Independent `scripts/phase9_profile_gate.py verify` replays all retained links and costs. Production commits: `6522a2d`, `86497e0`.

## Verification

- Task 1 selector: 2 passed. Task 2 selector: 1 passed. Full profile module: 3 passed.
- Retained gate independent verification passed with SHA-256 `17cbd088462b1139325d017372fd416ef7b5addd350a05d12f6aa230db971d81`.

## Self-Check: PASSED

The measured fixture and replay gate exist, are verified, and keep publication scheduling denied.
