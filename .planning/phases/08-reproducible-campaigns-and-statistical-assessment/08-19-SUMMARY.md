---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "19"
subsystem: paired canonical campaign definition
tags: [campaigns, paired-sampling, canonical-bp, provenance, slurm]
requires:
  - phase: 08-18
    provides: installed paired report and route-verification lifecycle
provides:
  - hash-bound BB-144 p=0.05 fast and relay manifests with shared physical sampling
  - strict two-sample, two-arm campaign work specification and four-unit frozen plan
  - read-only paired preflight and documented bounded lifecycle
affects: [phase-08, phase-11, campaign-execution]
tech-stack:
  added: []
  patterns:
    - paired preflight validates the strict work document without creating an output directory
    - paired artifacts use campaign-work-plan.json, while legacy one-unit artifacts retain campaign-plan.json
key-files:
  created:
    - data/manifests/phase8-paired-bb144-fast.json
    - data/manifests/phase8-paired-bb144-slow.json
    - data/studies/phase8-paired-canonical-gate-v1.json
    - data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json
  modified:
    - src/bp_registry/campaigns/cli.py
    - docs/campaigns.md
    - tests/test_campaign_execution.py
decisions:
  - "Use one immutable p=0.05 BB-144 sampler contract for two fast/relay policy arms and sample IDs 0 and 1."
  - "Retain paired plan bytes as campaign-work-plan.json, the installed strict-work artifact name."
actuals:
  tokens: 7399
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 5da1d3a5fa41f5ef41d0b8bb0d583f5cfb176880
duration: 44min
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 19: Paired Canonical Gate Summary

**A real BB-144 p=0.05 fast/relay pair now freezes two shared physical samples, four bounded units, and an installed lifecycle that denies production dispatch without measured site ceilings.**

## Accomplishments

- Added distinct fast and relay canonical manifests that retain their real policy behavior while matching artifact bytes, CSS code-capacity channel, error rate, seed, sample namespace, sampler derivation, environment contract, and two-shot budget.
- Added a strict `campaign_work_spec_v1` with two arms, sample IDs `0` and `1`, fixed two-shot stopping, complete outcome treatment, all-domain development target, frozen caps, target-arm mapping, source-denominator status, and source/environment/dependency locks.
- Produced and independently reloaded the exact `campaign-work-plan.json` artifact, which contains exactly four units and two bounded shards without generating materialized samples or result evidence.
- Extended installed `preflight` to validate paired work documents through the existing strict parser and exact arm checks while returning `sampling_performed: false` and leaving the specified output root absent.
- Documented local, selected-Slurm, merge, resume, assessment, report verification, and route verification commands; the historical rate-mismatched one-shot pair remains synthetic transport/recovery evidence only.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign preflight --campaign data/studies/phase8-paired-canonical-gate-v1.json --campaign-root . --output-root data/results/phase8-paired-canonical-gate-v1` — passed; returned `sampling_performed: false` and did not create the output root.
- `OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign plan --campaign data/studies/phase8-paired-canonical-gate-v1.json --campaign-root . --output-root data/results/phase8-paired-canonical-gate-v1` — passed; created a hash-bound plan with four units and two shards.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'paired_canonical_gate_definition_and_documented_lifecycle' -x` — passed (1 selected).
- The broader plan command began but its execution host detached before returning an exit status. The Phase 08 coordinator will run the full suite once after Plan 08-20, with durable exit capture.

## Task Commits

1. Task 1: `27a9777` — `feat(08-19): freeze paired canonical campaign inputs`
2. Task 2: `8b33c92` — `docs(08-19): document paired canonical campaign lifecycle`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking integration] Add strict paired preflight dispatch**

- **Found during:** Task 1 preflight.
- **Issue:** `preflight` accepted only the legacy `campaign_spec` document and rejected the required strict `campaign_work_spec_v1` before its no-write validation could run.
- **Fix:** Route paired documents through `_work_document` and `_work_plan_payload`, preserving legacy preflight behavior and returning the existing no-write response shape.
- **Files modified:** `src/bp_registry/campaigns/cli.py`
- **Commit:** `27a9777`

**2. [Rule 3 - Blocking integration] Correct paired plan artifact references**

- **Found during:** Task 1 plan publication.
- **Issue:** The installed paired command publishes `campaign-work-plan.json`; the prior Plan 08-19 artifact reference named the legacy `campaign-plan.json` artifact.
- **Fix:** Corrected Plan 08-19 and downstream Phase 08 verification references to the installed paired artifact name.
- **Files modified:** `.planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-19-PLAN.md`, `.planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-20-PLAN.md`, `.planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-VALIDATION.md`
- **Commit:** `5da1d3a`

## Known Stubs

None.

## Deferred Verification

- The broad required campaign regression did not return a durable exit status from this executor. The coordinator owns its final rerun after Plan 08-20 so the suite runs once against the complete paired lifecycle.

## Self-Check: PASSED

- The paired manifests, study, frozen work plan, documentation, regression, and summary exist.
- Commits `5da1d3a`, `27a9777`, and `8b33c92` are present in Git history.
