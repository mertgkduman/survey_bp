---
phase: 01-evidence-registry-and-native-css-baseline
plan: 06
subsystem: evidence-registry
tags: [systematic-mapping, provenance, jsonl, css-code-capacity, bpgd, impulse-decoding]
requires:
  - phase: 01-03
    provides: native CSS tracer and append-only provenance patterns
provides:
  - Versioned mapping protocol with reproducible source queries and screening rules
  - Lock-protected JSONL event history that preserves raw search hits and revisions
  - Source-anchored BPGD and impulse CSS figure/table inventories with explicit evidence maturity
affects: [01-08, 01-09, evidence-mapping, reproduction-registry]
tech-stack:
  added: []
  patterns: [content-addressed event identity, append-only screening, claim-state and maturity separation, source-anchored extraction]
key-files:
  created: [src/bp_registry/evidence.py, data/evidence/protocol.json, data/evidence/events.jsonl, data/evidence/seed-records.json]
  modified: [tests/test_evidence.py]
key-decisions:
  - "Graph-only curve values remain explicitly unavailable until author data or a documented digitization method is recorded."
  - "A paper claim stays mapped_only when a distinct pilot run is merely reserved or has not run."
  - "B1, C2, and BB-144 parameter labels are source leads; they do not establish matrix or logical-basis identity."
patterns-established:
  - "Stable event IDs make identical repeated imports idempotent while rejecting altered payloads under the same ID."
  - "Raw hit identity, normalized work identity, and revision identity persist as separate fields."
requirements-completed: [MAP-01, MAP-02, MAP-03, REG-04]
coverage:
  - id: D1
    description: Versioned mapping protocol and append-only, replayable screening trail
    requirement: MAP-01
    verification:
      - kind: unit
        ref: tests/test_evidence.py#test_protocol_has_reproducible_mapping_fields
        status: pass
      - kind: unit
        ref: tests/test_evidence.py#test_screening_history_reloads_in_original_order
        status: pass
    human_judgment: false
  - id: D2
    description: Idempotent duplicate handling and source/revision-aware event provenance
    requirement: MAP-02
    verification:
      - kind: unit
        ref: tests/test_evidence.py#test_repeated_and_concurrent_identical_imports_are_idempotent
        status: pass
      - kind: unit
        ref: tests/test_evidence.py#test_same_event_id_with_different_content_is_a_conflict
        status: pass
    human_judgment: false
  - id: D3
    description: BPGD and impulse CSS figure/table records with anchored taxonomy, ambiguity, and maturity
    requirement: MAP-03
    verification:
      - kind: unit
        ref: tests/test_evidence.py#test_seed_records_cover_named_css_figures_tables_and_deferred_regimes
        status: pass
      - kind: unit
        ref: tests/test_evidence.py#test_seed_claims_remain_anchored_queryable_and_maturity_safe
        status: pass
    human_judgment: true
    rationale: Source-to-record fidelity for the primary papers requires end-of-phase human comparison against the pinned revisions.
actuals:
  tokens: 10356
  tasks: 2
  commits: 4
plan_head_before: 315a9551348defe4a60d0158d3b3cb983b2680cd
duration: 9min
completed: 2026-09-22
status: complete
---

# Phase 01 Plan 06: Evidence Registry and CSS Paper Extraction Summary

**Versioned mapping evidence now preserves source identity and screening history while fully inventorying BPGD and impulse CSS results without promoting them to reproduction evidence.**

## Accomplishments

- Added a validated mapping protocol, event-sourced screening registry, stable event identities, and local writer locking for repeated or concurrent source imports.
- Recorded two targeted, observed arXiv seed resolutions without inventing corpus counts; raw hit, normalized work, and revision IDs remain distinct.
- Extracted BPGD Figures 2–6 and Table 1 plus impulse Figures 1–7 and Table I as source-anchored CSS records, including exact table values where the papers print them.
- Recorded BPGD Figures 7–8 as quaternary and impulse Figures 8–9 as circuit material that is identified but not extracted in this CSS pass.
- Kept paper experiments at `mapped_only`; the BB-144 pilot uses a distinct, not-run `pilot_adaptation` identifier and cannot promote the Figure 6 paper claim.

## Task Commits

1. **Task 1 RED:** `dfd7442` (`test`) — mapping protocol and event-history contracts.
2. **Task 1 GREEN:** `fce4023` (`feat`) — validated protocol and append-only evidence registry.
3. **Task 2 RED:** `24f8d94` (`test`) — CSS extraction coverage and maturity-separation contracts.
4. **Task 2 GREEN:** `91e0a52` (`feat`) — anchored BPGD and impulse seed records.

## Verification

- `python -m pytest -q tests/test_evidence.py` — **10 passed**.
- `PYTHONPATH=src python` inventory check — **passed** for BPGD Figures 2–6/Table 1 and impulse Figures 1–7/Table I.
- `python -m json.tool data/evidence/protocol.json` and `python -m json.tool data/evidence/seed-records.json` — **passed**.

## Decisions Made

- Preserved source claims (`established`, `inferred`, `unresolved`) separately from evidence maturity (`mapped_only`, `reference_executable`, `canonical_implemented`, `statistically_assessed`).
- Stored exact reported table cells only. Plot-derived points remain unavailable until a digitization method and uncertainty are recorded.
- Recorded C2 as hypergraph-product and B1 as lifted-product only where their respective sources say so; neither label resolves a code artifact identity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test correctness] Prevented an unrun pilot from being labeled reference-executable.**
- **Found during:** Task 2
- **Issue:** The initial test expectation would have assigned `reference_executable` to a reserved BB-144 pilot run that has not executed.
- **Fix:** Required `status: not_run` and `mapped_only` maturity until a completed run supplies independent evidence.
- **Files modified:** `tests/test_evidence.py`, `data/evidence/seed-records.json`
- **Verification:** `python -m pytest -q tests/test_evidence.py`
- **Committed in:** `91e0a52`

## Limitations

- No numeric curve points were inferred from figures. Each plot record states that author data or an auditable digitization method is still needed.
- BPGD and impulse author implementation identities remain unresolved; this records uncertainty rather than claiming absence.
- B1, C2, and BB-144 exact matrix and logical-basis identities remain future artifact-validation work.

## TDD Gate Compliance

- Task 1: RED `dfd7442` preceded GREEN `fce4023`; the intentional target assertion was verified as `RED_EVIDENCE_OK`.
- Task 2: RED `24f8d94` preceded GREEN `91e0a52`; the intentional target assertion was verified as `RED_EVIDENCE_OK`.

## Next Phase Readiness

Plans that freeze artifacts or run a pilot can attach their distinct run IDs to these source experiments without changing paper maturity automatically.

## Self-Check: PASSED

All five declared implementation/test files exist, all four RED/GREEN commits are present, and the focused evidence suite passes.
