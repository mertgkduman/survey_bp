# Phase 6 Revision: Matched Initial BP, Relay Legs, Beam Branches

**Decision date:** 2026-10-04
**Authority:** User instruction: “implement beam search and relayBP with fair initial BP runs and additional legs ... instead of the previous plan, add damping to those.”

## Locked implementation direction

1. Use a common CSS code-capacity min-sum BP initial stage for the controlled BeamSearch and RelayBP comparison. It has the same observation, numerical profile, flooding order, iteration cap, stopping rule, V2C damping coefficient, and physical sample. Both extensions receive the identical decoder-visible initial state; if it converges, both stop with the same candidate and zero extra work.
2. Count an **additional Relay unit** as one disordered-memory DMem-BP run *after* the common initial stage. It receives only the previous posterior, resets its edge messages and V2C damping state, and draws a fresh seeded per-variable memory-strength vector from an explicitly declared interval. The original Relay paper calls its first memory-BP run leg 0, so this controlled plain-BP initial stage plus additional-leg count is a labeled adaptation, never the source procedure.
3. Count an **additional Beam unit** as one decimated/masked branch after the common initial stage. Branch on the least reliable unmasked variable; fix 0/1, transform the syndrome, exclude masked nodes and edges, warm-start surviving V2C messages, accumulate posterior reliability, and preserve pruned/denied branches. Source-qualified BeamSearch uses min-sum; SPA is a separate adaptation if added later.
4. Use optional V2C damping with fresh-message coefficient gamma=0.5, per the user's earlier explicit setting, on the common initial run and on each additional unit. The off control is gamma=1.0. Relay's disordered prior-memory gamma is a different variable and is not replaced by V2C damping.
5. Apply the same maximum extra check-to-variable update budget to each extension, but show actual typed work and runtime separately. A unit count does not imply equal computational cost. Select only original-syndrome-valid candidates using declared channel-prior weight and stable ties.
6. Prespecify later evaluation samples and selection samples separately. The current eight-shot BB72 fixture is implementation evidence marked `not_assessed`, with no performance ranking.

## Relationship to source and earlier artifacts

- Source BeamSearch: [Ye, Wecker, Delfosse, arXiv:2512.07057v2](https://arxiv.org/html/2512.07057v2). Its initial BP and masked branch flow inform the controlled CSS implementation. Its reported circuit-level results are a separate reproduction target.
- Source RelayBP: [Müller et al., arXiv:2506.01779v2](https://arxiv.org/html/2506.01779v2). Its DMem-BP affine prior and posterior transfer inform the additional legs. Its paper-defined first leg, parameters, and circuit-level results remain separate.
- The old 06-01 through 06-10 plans, their validation/source audit, and their PASS report are archived under `superseded-20261004/`. Their PASS verdict applies only to the former AutDEC/BeamSearch ordering. The Phase 6 plan must be rebuilt around this user decision before `$gsd-execute-phase 06` is used.
- The Phase 5 notebook visual UAT remains open. This explicit implementation request authorizes independent controlled development while that visual review is pending; it does not mark the review passed.
- The sealed BB72 BP-SF v2 run remains in the original checkout. Development occurs in `feat/fair-damped-beam-relay`; merge into main only after the v2 run and publisher finish.

## Current planning baseline (2026-10-05)

The BB72 BP-SF v2 and matched BeamSearch/RelayBP work have since been published to `main`; the preceding branch/run condition is historical. Replan from the tracked implementation and verified evidence currently on `main`, without rerunning a completed campaign by default.

The user approved the [three-paper CSS literature gate](06-LITERATURE-GATE.md) as an additional Phase 6 acceptance slice. Its 14 paper-root `.spec.toml` records are source specifications, not executable decoder files. Make the kernel-readable policy-file route and bounded B1 execution concrete first, while preserving the controlled BeamSearch/RelayBP decisions above and leaving full publication-curve assessment to Phases 8–9.
