# Phase 1 Multi-Source Coverage Audit

All source items below are covered by a numbered plan. The requirements row points to the plan that completes its behavior; Wave 0 may also scaffold its tests. Deferred quaternary/circuit extraction, canonical BPGD/impulse execution, and statistical assessment are excluded by CONTEXT.md and ROADMAP.md.

| Source | ID/item | Plan(s) | Status | Evidence in plan |
|---|---|---|---|---|
| GOAL | Source-linked paper to validated native CSS outcome and provenance | 03, 06, 07, 08, 09 | COVERED | Tracer then source, artifact, preflight, pilot, result |
| REQ | MAP-01 protocol | 06 | COVERED | Questions, search/query/cutoff, screening, adjudication, snowballing, extraction |
| REQ | MAP-02 corpus trail | 06, 09 | COVERED | Raw hits, dedup, revisions, decisions, search provenance, linked pilot |
| REQ | MAP-03 taxonomy | 06, 08, 09 | COVERED | Claim-level dimensions, ambiguity, code relations, query |
| REQ | REG-01 complete manifest | 07, 09 | COVERED | Strict fields, schema, selected pilot manifest |
| REQ | REG-02 immutable resolution | 04, 07, 08 | COVERED | Root confinement and raw/semantic hash preflight |
| REQ | REG-03 pinned native run | 03, 08, 09 | COVERED | Real SDK tracer, verified publication artifact, local pilot |
| REQ | REG-04 evidence states | 06, 09 | COVERED | Paper/pilot records and separate maturity/assessment labels |
| REQ | CSS-01 check and logical validation | 04, 08 | COVERED | GF(2) algebra and selected source artifact |
| REQ | CSS-02 stable ordered hashes | 04, 08 | COVERED | Canonical bytes, golden tests, source and semantic digests |
| REQ | CSS-03 identified bit-flip sampling | 04, 09 | COVERED | Seed derivation, X/Z observations, 32 shot IDs |
| REQ | CSS-04 four outcome classes | 04, 09 | COVERED | Independent constructed fixtures and pilot evaluator |
| REQ | LED-01 every shot final | 03, 05, 09 | COVERED | Begin/final journal, reconciliation, denominator reconstruction |
| RESEARCH | BPGD/impulse CSS extraction and later-regime identification | 06 | COVERED | Named figure/table coverage and exact source anchors |
| RESEARCH | B1 lifted product, C2 HGP, Gross BB family | 06, 08 | COVERED | Distinct candidate inventory and source decision rubric |
| RESEARCH | Conditional BB-144 source/logical gate | 08, 09 | COVERED | Freeze only after exact rows, logical extraction and algebra; alternate verified candidate or blocker |
| RESEARCH | Local Python/SDK version probe and SUS package audit | 01, 02, 03 | COVERED | Environment identity, blocking-human legitimacy, exact-version install |
| RESEARCH | Strict manifest, artifact identity, CSS oracle, native adapter | 03, 04, 07, 09 | COVERED | Tracer and expanded validation |
| RESEARCH | Begin/terminal evidence, honest maturity states | 05, 06, 09 | COVERED | Typed JSONL, interrupted repair, separate paper/pilot states |
| RESEARCH | ASVS L1 local CLI boundaries | 01–09 | COVERED | Every plan has a STRIDE threat model and high-severity mitigations |
| CONTEXT | D-01 first fully extracted BPGD and impulse seeds | 06 | COVERED | Source-linked variants, settings, reported results and ambiguity |
| CONTEXT | D-02 full CSS extraction, other regimes identified | 06 | COVERED | Named CSS figures/tables; quaternary/circuit IDs only |
| CONTEXT | D-03 HGP, B1, Gross inventory and identity gate | 06, 08 | COVERED | Distinct source relations and artifact criteria |
| CONTEXT | D-04 choose first baseline by completeness | 08, 09 | COVERED | Candidate rubric, rejected reasons, no preferred family |
| CONTEXT | D-05 pinned native pilot when source settings unavailable | 03, 09 | COVERED | `pilot_adaptation` and `not_assessed` across surfaces |

## Spec-less Edge Probe Assumptions

No Phase 1 SPEC exists. The deterministic fallback returned 18 applicable edge proposals and no resolved decisions. These are planning assumptions until execution evidence resolves them; no proposal is dismissed silently.

| Requirement | Surfaced shape | Planned resolution |
|---|---|---|
| MAP-02 | adjacency, empty, ordering | Plan 06 tests adjacent duplicate hits, zero-result searches, ordered revision/decision reload. |
| MAP-03 | idempotency, concurrency | Plan 06 tests repeated and concurrent same-ID claim/event imports with conflict handling. |
| CSS-03 | boundary, precision | Plan 04 tests rates 0 and 1, nonfinite/out-of-range rejection, and decimal rate round-trip. |
| LED-01 | adjacency, empty, ordering | Plan 05 tests adjacent begin/final pairs, empty journal, order errors, duplicates, and reconciliation. |
| MAP-01, REG-01–04, CSS-01–02, CSS-04 | unclassified by probe | Plans 03–09 provide explicit field, invalid-input, algebra, lifecycle, and status acceptance criteria; no extra probe predicate was inferred for these rows. |

## Spec-less Prohibition Recall

The bespoke intent risks are scientific overclaim and false source identity. Descriptor-less flagged-unverified prohibitions appear in Plans 06 and 09 so verification cannot silently treat them as checked. Generic path traversal, package integrity, and resource exhaustion are handled in the plans' ASVS L1 threat models rather than duplicated as bespoke prohibitions.

## External SDK Coverage

This phase genuinely integrates the external `ldpc.BpDecoder` SDK through `NativeBpReference`. Plan 03 probes the actual installed constructor, `decode`, `converge`, and `iter` behavior; Plan 09 pins the distribution version and tests a tiny real syndrome, unsupported API/version behavior, and the runner-to-adapter boundary. There is no HTTP API integration in Phase 1.
