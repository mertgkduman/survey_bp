---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "01"
subsystem: research-policy-interface
tags: [toml, canonical-css, provenance, cache, verification]
requires:
  - phase: "05"
    provides: Canonical CSS schemas 5 and 6 with bounded intervention and damping controls
provides:
  - Strict runnable and non-runnable literature-policy TOML parsing
  - Common canonical study dispatch through schemas 2 through 6
  - Verified shared-computation cache with immutable request provenance receipts
affects: [06-02, literature-policies, reproduction-manifests]
actuals:
  tokens: 7065
  tasks: 2
  commits: 2
plan_head_before: 950743d20a2f0c59dcf542f6e9cf7796221eee58
tech-stack:
  added: []
  patterns: [closed TOML policy registry, executable-provenance-raw identity separation, append-only request receipt]
key-files:
  created: [src/bp_registry/literature.py, literature_policies/yao-2024-guided-decimation/bp-t100.toml, tests/test_literature_policy.py]
  modified: [src/bp_registry/study.py, tests/test_study_entrypoint.py]
key-decisions:
  - "Only the registered executable role projection reaches the canonical manifest; source prose cannot affect numerical identity."
  - "A verified computation cache is shared by executable identity, while each raw policy document writes a separate immutable receipt."
requirements-completed: [INT-05, CAN-01]
coverage:
  - id: D1
    description: Strict literature-policy parsing and typed non-runnable preflight before artifact resolution.
    requirement: INT-05
    verification:
      - kind: integration
        ref: tests/test_literature_policy.py#test_non_runnable_source_record_returns_before_artifact_loading
        status: pass
    human_judgment: false
  - id: D2
    description: Common TOML command path for the qualified Yao binary-BP comparator and verified cache reuse.
    requirement: CAN-01
    verification:
      - kind: e2e
        ref: bp-registry /tmp/bp-study-npsckV/study.json --decoder literature_policies/yao-2024-guided-decimation/bp-t100.toml
        status: pass
      - kind: integration
        ref: tests/test_literature_policy.py#test_tracer_bp_t100_common_command_computes
        status: pass
    human_judgment: false
  - id: D3
    description: Metadata-distinct policy documents reuse verified computation while preserving individual receipts.
    verification:
      - kind: integration
        ref: tests/test_literature_policy.py#test_shared_compute_keeps_append_only_request_receipts
        status: pass
    human_judgment: false
duration: 14min
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 01: Literature policy command path Summary

**A strict TOML policy compiler now runs a qualified Yao binary-BP adaptation through canonical CSS execution, verification, reuse, and immutable source-document receipts.**

## Performance

- **Duration:** 14 min
- **Tasks:** 2/2
- **Files modified:** 5
- **Tests:** 13 focused parser and study-entrypoint tests passed.

## Accomplishments

- Added a closed parser that separates executable policy controls, normalized source provenance, and raw document bytes. Non-runnable `.spec.toml` records return a typed disposition before the study or artifact is read.
- Added a runnable `bp-t100.toml` policy for Yao et al.'s binary BP comparator. It is explicitly a canonical adaptation and preserves the unresolved paper-artifact and author-code identities.
- Extended policy-free study compilation through canonical schemas 5 and 6, with intervention, damping memory, and stopping controls owned by the decoder document.
- Replaced cache-only attribution with a verified computation receipt plus write-once per-request receipts. Raw comment or source-prose changes remain traceable without changing numerical execution identity.

## Task Commits

1. **Task 1: Execute one paper policy through the common study command** — `9af209d` (`feat`)
2. **Task 2: Separate computation reuse from request provenance** — `8bf3bde` (`feat`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -x` — 13 passed.
- Installed the current project editable with `--no-deps`, then ran `bp-registry` against a bounded three-qubit study and `bp-t100.toml`: first computed a verified two-shot result and the next invocation reused it.
- Reconstructed complete schema-5 and schema-6 manifests after moving decoder-owned controls out of the study; both parsed as their respective public manifest type.

## Decisions Made

- The decoder-owned stopping cap must equal every public study budget cap. This makes the policy's iteration limit part of the persisted executable manifest instead of inert metadata.
- Receipt identities bind the computation key, executable projection, normalized provenance, raw bytes, and source-path label. Verification timestamps are excluded so repeated requests have stable immutable receipt content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Installed the repository editable to expose its declared `bp-registry` console script.**

- **Found during:** Task 1 command smoke test.
- **Issue:** The active virtual environment could import the package but did not contain the console-script wrapper declared in `pyproject.toml`.
- **Fix:** Ran `.venv/bin/pip install --no-deps -e .`; no project files or dependencies changed.
- **Verification:** The installed command computed and then reused the bounded verified result.

**Total deviations:** 1 auto-fixed (Rule 3).

## Known Stubs

None.

## Next Phase Readiness

The policy-file boundary is ready for the Phase 6 intervention and ensemble policy files. The runnable Yao policy remains a bounded canonical adaptation until its source B1 artifact and complete published experiment settings are reconciled.

## Self-Check: PASSED

- Confirmed the five planned implementation/test/policy files exist.
- Confirmed task commits `9af209d` and `8bf3bde` exist in repository history.
