# Phase 7 Multi-Source Coverage Audit

All four required source types are covered. Deferred Phase 8–13 work is recorded as an exclusion and does not appear as implementation scope.

| SOURCE | ID | Feature / constraint | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Attach independently configurable additional processing to canonical BP nonconvergence while retaining clear BP-only evidence | 07-01, 07-07, 07-11–07-13, 07-09, 07-10 | COVERED | The tracer is publicly runnable; snapshot, admission, evidence, CLI, and notebook plans expand it. |
| REQ | POST-01 | Canonical OSD with explicit handoff, method/order, trigger, and work | 07-02, 07-03, 07-07, 07-12, 07-13, 07-14, 07-09 | COVERED | Exact official standalone seam is trust-gated, isolated, qualified, replayed, and exposed publicly. |
| REQ | POST-02 | Canonical LSD with explicit handoff, method/order, trigger, and work | 07-01, 07-07, 07-11–07-14, 07-09 | COVERED | Released standalone LSD is the public tracer and gains MBBP whole-composition support. |
| REQ | POST-03 | Source-resolved SI inactivation, BP rerun/solve, reconstruction, compatibility | 07-04, 07-07, 07-12, 07-13, 07-15, 07-09 | COVERED | Faithful blockers remain spec-only; verified deterministic CSS adaptation is separately named. |
| REQ | POST-04 | Source-resolved OTF graph construction/pruning, BP rerun, reconstruction, compatibility | 07-05, 07-07, 07-12, 07-13, 07-15, 07-09 | COVERED | Binary-CSS adaptation is explicit; faithful circuit path remains later. |
| REQ | POST-05 | Disable/trigger, retain BP-only/final, and run pinned native composites separately | 07-01, 07-06, 07-07, 07-09–07-13 | COVERED | Native BP identity and opaque missingness stay distinct. |
| CONTEXT | D-01 | Trigger only after the entire BP/search composition fails | 07-01, 07-07, 07-11, 07-12 | COVERED | Base tracer plus MBBP snapshot propagation; every other pair fails closed at preflight. |
| CONTEXT | D-02 | Deterministic truth-free failed-attempt ranking | 07-01, 07-11, 07-12 | COVERED | Every compatible base/MBBP attempt reaches the residual/NLL/ordinal/lineage key. |
| CONTEXT | D-03 | Explicit method handoff, reliability translation, reconstruction, original validation | 07-01, 07-03–07-05, 07-07, 07-11, 07-12 | COVERED | Each method and supported composition has an explicit compatibility contract. |
| CONTEXT | D-04 | Errors/unusable reliability skip fallback and retain BP terminal | 07-01, 07-07, 07-11, 07-12 | COVERED | Typed incompatibility, skip, and error grammar. |
| CONTEXT | D-05 | At most one OSD/LSD/SI/OTF method; method-owned SI/OTF subwork | 07-01, 07-03–07-05, 07-07, 07-12 | COVERED | Closed one-method schema and one fallback call. |
| CONTEXT | D-06 | Source-specific versus controlled scoring and stable ties | 07-01, 07-03, 07-07, 07-08, 07-12, 07-14, 07-15 | COVERED | Separate labels and complete candidate provenance. |
| CONTEXT | D-07 | No valid fallback retains BP output without false success | 07-01, 07-03–07-05, 07-12 | COVERED | Typed unsuccessful method results and exact replay. |
| CONTEXT | D-08 | Valid candidate survives later cap; incomplete/invalid does not | 07-01, 07-03–07-05, 07-12 | COVERED | Method fixtures plus replay enforce candidate-before-cap. |
| CONTEXT | D-09 | Complete seven-role paper-linked TOML with postprocessing | 07-08, 07-14, 07-15 | COVERED | Costly compiler shape and published files are separated. |
| CONTEXT | D-10 | Separate BP/fallback source anchors and composite distinction | 07-08, 07-14, 07-15 | COVERED | Component provenance is required and identity-separated. |
| CONTEXT | D-11 | Complete paper files plus resolved controlled fallback arms | 07-08, 07-09, 07-14, 07-15 | COVERED | Resolved manifests/receipts precede execution. |
| CONTEXT | D-12 | Non-runnable SI/OTF faithful specs beside qualified adaptations | 07-04, 07-05, 07-15 | COVERED | Honest blockers and adaptation labels are published and tested separately. |
| CONTEXT | D-13 | Durable CLI/ledger and compact shot-first notebook | 07-01, 07-09, 07-10, 07-12, 07-13 | COVERED | Public tracer, complete run/verify, and digest-bound notebook/HTML. |
| CONTEXT | D-14 | Same B1 samples across BP-only, canonical fallbacks, and native composites | 07-06, 07-09 | COVERED | Two samples × seven arms; native identity stays separate. |
| CONTEXT | D-15 | B1 primary view plus focused deterministic mechanism fixtures | 07-01, 07-03, 07-04, 07-05, 07-09, 07-10 | COVERED | Fixtures are not cross-code performance evidence. |
| CONTEXT | D-16 | Retain every B1 shot; separate trigger/no-trigger fixtures; bounded labels | 07-09, 07-10 | COVERED | All fourteen rows required; `pilot_adaptation`/`not_assessed`. |
| RESEARCH | — | Released LSD and native composites use exact ldpc 2.4.1 APIs | 07-01, 07-06 | COVERED | External API matrix lists exact surfaces and drift tests. |
| RESEARCH | — | Released package has no standalone OSD; official divergent branch needs isolated qualification | 07-02, 07-03 | COVERED | Blocking legitimacy gate plus committed receipt. |
| RESEARCH | — | SI v3 has unresolved deterministic conventions | 07-04, 07-15 | COVERED | Faithful spec stays non-runnable; adaptation is explicit. |
| RESEARCH | — | OTF source/code is circuit-oriented and unfinished for faithful Phase 7 transfer | 07-05, 07-15 | COVERED | CSS adaptation only; no BPOTF runtime dependency. |
| RESEARCH | — | Frozen handoff, strict compatibility, one-method subwork, and complete evidence | 07-01, 07-07, 07-11–07-13 | COVERED | Core tracer, supported-composition snapshots, fail-closed admission, replay, and CLI. |
| RESEARCH | — | No hidden truth; original problems immutable; unavailable work is not zero | 07-01, 07-03–07-07 | COVERED | Threat models and tests cover each boundary. |
| RESEARCH | — | Finite matched B1 mechanism view retaining every shot | 07-09, 07-10 | COVERED | Reuses verified B1 artifact/sample namespace with exact caps. |

## Qualification-gate disposition

No feasibility question remains open for planning. POST-01 has an exact source/build/API pass gate whose failure leaves the method blocked. Under D-12, source-faithful SI and circuit OTF remain non-runnable with honest blockers, while only separately named adaptations can pass their algebra/graph fixtures. Descriptor-less bespoke prohibitions remain in `must_haves.prohibitions`; no `check_*` descriptor was invented.

## Explicit exclusions

- Phase 8 owns campaign scale, statistical criteria, throughput profiling, and denominator methodology beyond this fixed all-terminal mechanism view.
- Phase 9 owns CSS paper-curve assessment, controlled performance claims, and public policy-file voting.
- Phases 10–11 own correlated quaternary execution/assessment.
- Phases 12–13 own circuit transfer, detector/observable semantics, faithful circuit OTF, and circuit source assessment.
