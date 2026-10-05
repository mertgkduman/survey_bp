---
quick_id: 261005-2b9
status: in_progress
date: 2026-10-05
---

# Merge fair damped BeamSearch and RelayBP after BB72 v2 publication

1. Wait for Slurm continuation `57637301` to finish successfully and confirm the verified BB72 BP-SF factorial v2 package reached `origin/main`. Retain a failure as a blocker; do not bypass the publication check.
2. After a successful publication job, fetch the new main commit and merge `feat/fair-damped-beam-relay` in a clean worktree, preserving both the study package and Phase 6 revision. Stop on conflicts for review.
3. Run the focused Beam/Relay tests and eight-shot deterministic replay against the merged tree. Confirm the BB72 publication files and Git tree, then push the merged commit to `origin/main`.
4. Record the exact merge commit and verification in this quick task and project state. A dependent Slurm merge job may run the gates automatically after publication; it must fail closed if the publication is absent or the remote moves.
