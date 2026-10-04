# Phase 6 Multi-Source Coverage Audit

This audit covers the ROADMAP goal, every Phase 6 requirement, implementation-relevant research findings, and the absence of a Phase 6 CONTEXT.md. Items explicitly scoped to later performance campaigns or other decoding regimes are excluded.

| Source | ID | Feature or constraint | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Execute branching/ensemble searches and inspect generation, pruning, selection, voting, and cost | 02-10 | COVERED | Tracer through integrated audited fixture. |
| REQ | MOD-04 | Source-linked canonical BeamSearch plus pinned original reference where available | 02, 05, 07-10 | COVERED | Paper/C++ variants, native boundary, public run, replay. |
| REQ | INT-05 | Explicit member/parent identity, state sharing, limits, topology, and aggregate work | 03, 05-08, 10 | COVERED | Stable DAG, unique leaves, topology-independent logical order. |
| REQ | CAN-01 | Complete candidate list with eligibility, score, tie, origin, and rejected candidates | 03-08, 10 | COVERED | Frozen list plus exact replay. |
| REQ | CAN-02 | Declared voting object/electorate and independently checked final output | 03-04, 06-08, 10 | COVERED | Exact plurality and coordinate majority including invalid fixture. |
| RESEARCH | Phase 5 dependency | Complete pending visual notebook/HTML UAT before execution | 01 | COVERED | Blocking human gate; never auto-passed. |
| RESEARCH | Package legitimacy | All 14 BeamSearch requirements are SUS and require concrete human identity/hash approval before install | 09 | COVERED | Plan 09 independently validates source digests, dependency closure, target tags, exact wheel coverage, and recomputed hashes before approval, then installs only that approved set offline. |
| RESEARCH | Active BB72 source seal | Do not modify canonical source until the sealed run/report chain is terminal | 02 | COVERED | Checkable execution precondition before the first source edit. |
| RESEARCH | Canonical architecture | Extend the configurable canonical binary-message engine with a kernel-generic mask/warm-start seam | 02 | COVERED | Source BeamSearch binds min-sum; SPA has a separate controlled-adaptation identity. |
| RESEARCH | Versioning | Add full V7, compact V8, ledger/work version 5; preserve older grammars | 03, 07-08 | COVERED | Golden historical round trips. |
| RESEARCH | Beam paper procedure | Initial BP, masked branching, cumulative-posterior rank, collective pruning, result quota, presets | 02, 05 | COVERED | Exact bounded fixtures and named presets. |
| RESEARCH | Paper/code divergence | Keep paper_v2_min_sum_plus_declared_ties and exact official_cpp_084a475_observed_min_sum initialization/reuse/pruning/tie rules separate | 05 | COVERED | Low-degree index-zero, no-eligible-variable reuse, and equal-score store-index fixtures preserve pinned behavior. |
| RESEARCH | Native reference | Pin commit 084a475..., create a digest-bound isolated environment, attempt the documented install/build, and retain exact evidence | 09 | COVERED | Missingness requires a demonstrated captured failure after the real attempt; no canonical-environment mutation or vendoring. |
| RESEARCH | Generic controller | Deterministic logical order independent of worker completion | 03, 05-08 | COVERED | Identity, event, and reversed-worker tests. |
| RESEARCH | AutDEC model | Staged U_A/A automorphisms, independent members, direct original-coordinate correction check, min-weight selection/fallback | 06 | COVERED | Tests U_A H = H A, (H A)c=U_A s, and Hc=s without inverse mapping. |
| RESEARCH | Candidate retention | Preserve rejected, pruned, duplicate, late, and budget-denied origins | 03-05, 08, 10 | COVERED | Complete-tree fixture and exact work. |
| RESEARCH | Voting | Implement exact plurality and coordinate majority as canonical_generic | 04, 06-08, 10 | COVERED | No false paper attribution. |
| RESEARCH | Cost semantics | Separate aggregate typed work, observed runtime/resources, and DAG critical-path span | 03, 07-08, 10 | COVERED | No universal cost scalar or idealized measured latency. |
| RESEARCH | Public evidence | Strict preflight, member/vote events, frozen selection, truth boundary | 07 | COVERED | Rejects incompatible inputs before sampling. |
| RESEARCH | Structural replay | Reconstruct tree, identities, outcomes, work; reject rehashed semantic tampering | 08 | COVERED | Runtime values remain observational. |
| RESEARCH | Validation fixtures | Min-sum tree, index-zero/reuse divergence, equal ties, nontrivial automorphism, invalid vote, native status | 02-06, 08-10 | COVERED | Hand-audited deterministic fixtures. |
| RESEARCH | Security | Treat manifests, staged transforms, native checkout/output as untrusted | 02-10 | COVERED | Strict bounds, confinement, digests, original checks. |
| RESEARCH | Claim limits | CSS canonical adaptation, circuit-level paper, development_fixture/not_assessed | 05, 09-10 | COVERED | Machine-readable source-status matrix. |
| RESEARCH | Environment | Add no native dependency to canonical environment | 09 | COVERED | Requirements install only inside the confined stage; resolved lock and package hashes are retained. |
| CONTEXT | — | No Phase 6 CONTEXT.md exists | 01-10 | COVERED | User authorized autonomous planning from PROJECT, ROADMAP, REQUIREMENTS, RESEARCH, and PATTERNS. |

## Dependency graph

```text
06-01 Phase 5 visual UAT gate
  -> 06-02 masked canonical-BP tracer
    -> 06-03 versioned identities/work/ledger
      -> 06-04 list and vote policies
        -> 06-05 BeamSearch variants ----+
        -> 06-06 ensemble semantics ------+-> 06-07 public manifest/execution -> 06-08 replay
                                                          +-> 06-09 dependency approval + isolated native reference
        06-05 + 06-06 + 06-08 + 06-09 -----> 06-10 integrated audit/docs
```

No source item is unplanned. No deferred item is pulled into Phase 6. The active source-sealed BB72 study is outside every plan's file list.
