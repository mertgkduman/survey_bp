---
status: complete
quick_id: 261005-2b9
date: 2026-10-05
---

# Verified BeamSearch/RelayBP merge published

The sealed BB72 BP-SF factorial v2 continuation job `57637301` completed successfully and published its verified 24-arm package to `origin/main` at `0398c702da092d7a3734704938fb8c9519519a63`. Its recovered final arm reached the fixed 1,280-shot denominator. The original afterok publisher was canceled by the recovery script as designed.

Dependent merge job `57672074` merged `feat/fair-damped-beam-relay` onto that published commit in a clean worktree. It found no conflicts, passed 47 focused BeamSearch/RelayBP and Relay/memory tests, replayed the frozen eight-shot BB72 controlled fixture, and pushed merge commit `b84071e58f87e66c88ab472a5dc6437a5517c96a` to `origin/main`. The fixture remains `not_assessed` and does not support a decoder ranking.

The Phase 6 former plans remain archived and a full Phase 6 replan remains pending. The Phase 5 notebook visual UAT remains open.
