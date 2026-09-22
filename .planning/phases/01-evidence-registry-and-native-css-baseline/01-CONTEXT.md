# Phase 1: Evidence Registry and Native CSS Baseline - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the versioned literature mapping protocol and initial source records, a validated reproduction manifest and CSS mathematical foundation, and one pinned native binary BP pilot that emits identified outcomes and provenance. Phase 1 does not implement canonical BPGD or impulse policies or claim statistical reproduction of their curves.

</domain>

<decisions>
## Implementation Decisions

### Initial paper extraction
- **D-01:** Prioritize the BPGD and impulse-decoding papers as the first fully extracted seed records. Capture the source-defined algorithm variant, code and noise settings, reported results, implementation links, and unresolved details where available.
- **D-02:** In Phase 1, fully extract the CSS code-capacity experiments from those papers. Record other regimes as identified source material for later phase extraction; do not claim those experiments have been fully extracted now.

### Code inventory and first native run
- **D-03:** Include hypergraph product (HGP) codes used in BPGD papers, the B1 `[[882,24,18≤d≤24]]` candidate, and the Gross/bivariate-bicycle code family in the initial code inventory. Research must verify exact instance identities, matrices, logical bases, source revisions, and the relationship of each code to each paper before an executable manifest treats them as established.
- **D-04:** Select the first native binary BP baseline by completeness and verifiability of its paper, code, logical-operator, and implementation artifacts. There is no fixed first code family among HGP, B1, and Gross.
- **D-05:** When original paper code or exact settings are unavailable, a pinned, documented native BP reference may run on a verified code artifact as a **pilot adaptation**. Its registry status and results must not imply source-faithful reproduction or statistical assessment.

### Agent's Discretion
- Choose the exact Phase 1 HGP, B1, or Gross instance and pinned binary BP reference according to D-04, documenting rejected candidates and missing artifacts.
- Choose the practical local pilot shot count and output presentation while preserving the roadmap's per-shot ledger, termination, nonconvergence, and independent outcome requirements.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope and phase contract
- `.planning/PROJECT.md` — project architecture, research priority, reproduction meaning, and evaluation views.
- `.planning/REQUIREMENTS.md` — Phase 1 requirement definitions MAP-01–03, REG-01–04, CSS-01–04, and LED-01.
- `.planning/ROADMAP.md` — Phase 1 goal, boundary, and success criteria; later phases own named policy implementation and statistical assessment.

### Existing source research and safeguards
- `.planning/research/SUMMARY.md` — initial source inventory and unresolved source identities.
- `.planning/research/FEATURES.md` — mechanism and original-implementation anchors for BPGD and impulse decoding.
- `.planning/research/ARCHITECTURE.md` — proposed separation of runner, decoder, immutable original problem, evaluator, and evidence.
- `.planning/research/PITFALLS.md` — outcome, source-identity, and provenance hazards relevant to the first pilot.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No project implementation exists yet. The `.planning/research/` documents supply source leads and architecture proposals, not installed packages or validated code artifacts.

### Established Patterns
- The project requires source-linked claims, explicit unresolved identities, independent algebraic checks, and per-shot provenance before any result is promoted as reproduced.

### Integration Points
- New registry, manifest, CSS algebra/sampling/evaluation, and native reference code must be created during execution; there is no existing application module to integrate with.

</code_context>

<specifics>
## Specific Ideas

- User named BPGD and impulse decoding as priority papers. Candidate primary sources from initial scoping are [BPGD, arXiv:2312.10950](https://arxiv.org/abs/2312.10950) and [impulse decoding, arXiv:2606.18240](https://arxiv.org/abs/2606.18240); verify revisions and exact intended experiments during Phase 1 research.
- User connected HGP codes specifically to BPGD papers. B1 `[[882,24,18≤d≤24]]` and Gross `[[144,12,12]]` are source leads, not yet pinned project artifacts.
- If the native baseline cannot match a published experiment exactly, label the run and every downstream presentation as a pilot adaptation.

</specifics>

<deferred>
## Deferred Ideas

Full experiment extraction for quaternary and circuit-level regimes remains in their later roadmap phases. Canonical BPGD and impulse implementations and statistical curve assessment also remain in their assigned phases.

</deferred>

---

*Phase: 1-Evidence Registry and Native CSS Baseline*
*Context gathered: 2026-09-21*
