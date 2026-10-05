---
status: complete
quick_id: 261004-krc
date: 2026-10-04
---

# Fair damped BeamSearch and RelayBP implementation

Implemented a controlled BB72 CSS adaptation in `canonical/fair_legs.py`: each damping arm shares one exact initial min-sum BP result between BeamSearch and RelayBP. Beam extra units are masked, decimated branches; Relay extra units are disordered-memory BP legs. Damping uses the declared fresh V2C message coefficient, with `1.0` and `0.5` arms. The methods share an additional C2V work ceiling, while their actual work and every unit are recorded separately.

The eight-shot development fixture uses matched physical samples, a frozen design, an event ledger, deterministic replay, and independent original-problem outcome evaluation. Its `not_assessed` label prohibits a ranking claim. The common plain-BP initial stage differs from Relay's source-defined first memory-BP leg; BB72 CSS and damping are controlled adaptations of the cited circuit-level source experiments.

Verification: 47 focused/new plus Relay/memory tests passed after normalizing Beam path scores by current-branch iteration count per the source paper. The full isolated-worktree suite before that correction had 737 passed, 1 skipped, and 1 failure caused by a historical untracked Phase 4 cancellation receipt absent from the worktree; that test passed in the original workspace. The corrected eight-shot run and replay passed. The former Phase 6 plans were archived and new context recorded for a full replan.

The implementation is on `feat/fair-damped-beam-relay`. Mainline integration waits for the active sealed BB72 BP-SF v2 publication chain to finish. This quick task finishes the controller and development evidence, not the later statistical study or complete Phase 6.
