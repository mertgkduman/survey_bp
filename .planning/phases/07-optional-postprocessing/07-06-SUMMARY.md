---
phase: 07-optional-postprocessing
plan: "06"
subsystem: native reference arms
tags: [ldpc, bp-osd, bp-lsd, native-reference, matched-samples]
requires:
  - phase: 07-01
    provides: canonical postprocessing boundary kept distinct from native composite references
provides:
  - Pinned ldpc 2.4.1 BP-OSD and BP-LSD native composite adapters
  - Domain-separated native study arms with matched physical samples and explicit opaque-work missingness
affects: [07-optional-postprocessing, phase-08-campaigns]
tech-stack:
  added: []
  patterns: [closed native-arm controls, original-syndrome validation, native-composite cache identity]
key-files:
  created: []
  modified:
    - src/bp_registry/reference.py
    - src/bp_registry/study.py
    - tests/test_reference_smoke.py
    - tests/test_study_entrypoint.py
key-decisions:
  - "Treat BpOsdDecoder and BpLsdDecoder as native_composite_reference arms whose internal BP remains part of their own identity."
  - "Expose native iterations only as an observed SDK field and keep internal BP, fallback, edge, and control-flow work unavailable with reasons."
  - "Derive native study cache keys from a domain-separated composite arm identity so equal candidate bytes cannot merge a native arm with canonical evidence."
requirements-completed: [POST-05]
coverage:
  - id: D1
    description: Pinned native BP-OSD and BP-LSD adapters validate inputs, final candidates, identity, and opaque metric missingness.
    requirement: POST-05
    verification:
      - kind: unit
        ref: tests/test_reference_smoke.py
        status: pass
    human_judgment: false
  - id: D2
    description: Native composite study arms retain matched sample identities and distinct cache/provenance receipts.
    requirement: POST-05
    verification:
      - kind: integration
        ref: tests/test_study_entrypoint.py
        status: pass
    human_judgment: false
actuals:
  tokens: 7833
  tasks: 2
  commits: 4
plan_head_before: f00a0351446ad31034ba41e779d4805ef105f862
duration: 25min
completed: 2026-10-06
status: complete
---

# Phase 07 Plan 06: Native Composite Reference Arms Summary

Pinned `ldpc==2.4.1` BP-OSD and BP-LSD composites now execute as independently identified native references on matched CSS observations.

## Accomplishments

- Added strict BP-OSD and BP-LSD wrappers with explicit released constructor controls, package/provider identity, original-syndrome validation, typed success/nonconvergence/error/malformed terminals, and no canonical postprocessing dependency.
- Preserved native composite BP and final candidates while recording only exposed iterations; opaque internal BP, fallback, edge, and control-flow work remains explicitly unavailable.
- Added closed `native_bp_osd` and `native_bp_lsd` study arms that validate the exact pin before sampling, share the declared physical sample identity, and use cache/provenance identities disjoint from canonical execution.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py -k 'bp_osd or bp_lsd or composite or method or order or original or unavailable or malformed or error or identity' -x` — 6 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_study_entrypoint.py tests/test_reference_smoke.py -k 'native and (bp_osd or bp_lsd or matched or sample or cache or provenance or missingness or identity or override)' -x` — 8 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 839 passed, 1 skipped, 6 existing multiprocessing fork deprecation warnings; 14m 37s.

## TDD Gate Compliance

| Task | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| 1 | `.gsd/tdd-evidence/07-06-task-1-red.json` (`RED_EVIDENCE_OK`) | `ae2623b` | Passed |
| 2 | `.gsd/tdd-evidence/07-06-task-2-red.json` (`RED_EVIDENCE_OK`) | `82b5507` | Passed |

## Task Commits

1. `a1c0beb` — `test(07-06): add failing native composite adapter contract`
2. `ae2623b` — `feat(07-06): add pinned native composite references`
3. `f882a47` — `test(07-06): add failing native study arm contract`
4. `82b5507` — `feat(07-06): add matched native composite study arms`

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All four owned files and the summary exist. The four task commits are present in Git and match the measured plan range.
