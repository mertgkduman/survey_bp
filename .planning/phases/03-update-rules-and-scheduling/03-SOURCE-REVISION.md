# Phase 3 cluster source revision — 2026-09-24

## Decision and evidence status

The user confirmed that the authoritative Moradi clustered RL-S Q-table and ordered partition are unavailable, then selected Hsu, Chang, Su, and Weng, *A Non-Disjoint Group Shuffled Decoding for LDPC Codes*, arXiv:1202.1060v1, as the replacement Phase 3 cluster-sequential source. Preserve the Moradi loader and unavailable report as truthful mapped/source-gated evidence; do not reuse its artifact schema or attach its name to the new policy. SCH-06 remains pending until a source-linked public Hsu adaptation runs and verifies.

Primary source: https://arxiv.org/html/1202.1060 (version 1, 2012), Section II-C and its worked example in Section II-A.

## Source procedure and bounded configuration

Hsu et al. form ordered, overlapping check-node groups. Their worked example has group size 2 and overlap 1: `(c1,c2)`, `(c2,c3)`, `(c3,c4)`. For Phase 3, use this explicit source configuration: sample a permutation of all check IDs once per source iteration from a purpose-separated schedule RNG, then take consecutive adjacent pairs in that order. This is a deterministic replay rule for one source-consistent realization of the paper's random group construction, not a claim that the paper fixes a particular random seed or check order. Require at least two checks. Every check appears at least once, interior checks twice, and each successive pair overlaps by exactly one check.

For each group, evaluate its check-to-variable messages in parallel from the group's entry V2C snapshot; commit these, then refresh variable-to-check messages incident to variables adjacent to the group. Subsequent groups see the committed messages. This follows Section II-C's check update then variable update ordering. One group commit is the local work unit. The source checks the hard decision after a complete group traversal; project D-09 instead checks after each group and must label this stopping-cadence adaptation. Record the sampled permutation, realized groups, repeated check work, group cursor, full work vector, setup/decode runtime, and source iteration. A partial traversal is not rounded into a full iteration.

The source studies classical LDPC codeword decoding over BI-AWGN. The project will adapt the same binary Tanner-graph message-passing procedure to CSS bit-flip syndrome decoding using the measured syndrome. This requires independent small-graph semantic checks and a bounded public pilot; it does not reproduce the paper's reported curves or establish any QLDPC performance advantage. The source text has inconsistent general parameter notation in Section II-A, so Phase 3 pins the unambiguous size-2/overlap-1 worked construction rather than claiming a general `(G, N_G, r)` implementation.

Existing `LayeredSchedule` enforces no shared variable neighbors within a layer, while the Hsu source permits arbitrary check pairs and repeated checks across groups. Reusing a layer under a new label would silently change admissible behavior; implement a distinct schedule policy on the canonical binary BP engine. Keep the same immutable original problem and independent evaluator.

## Second paper supplied by user

Pradhan, Raveendran, Rengaswamy, and Vasic, *Linear Time Iterative Decoders for Hypergraph-Product and Lifted-Product Codes*, arXiv:2504.01728v1 (2025), https://arxiv.org/pdf/2504.01728, is not a cluster-sequential BP source. Algorithm 2 is trapping-set-aware bit flipping with separate VV/CC passes; Section VII-B alternates VV/CC variable-message updates in min-sum, and Section VII-C combines diverse decoders. Keep it as a mapped source lead for Phase 5 intervention and Phase 6 ensemble research. Its LP/HP structure, depolarizing setting, edge biases, and source experiments need separate qualification before any implementation or reproduction claim.
