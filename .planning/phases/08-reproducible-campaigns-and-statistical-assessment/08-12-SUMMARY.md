---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "12"
subsystem: campaign CLI
tags: [campaigns, cli, argparse, slurm, evidence, installed-command]
requires:
  - phase: 08-09
    provides: bounded local execution and sealed receipts
  - phase: 08-10
    provides: shell-free Slurm transport
  - phase: 08-11
    provides: evidence-only reporting contracts
provides:
  - Strict JSON campaign lifecycle command
  - Installed bp-registry-campaign entry point
  - Route-equivalence and fail-closed lifecycle coverage
affects: [phase-09-css-reproduction, phase-11-quaternary-reproduction, phase-08-campaigns]
tech-stack:
  added: []
  patterns: [strict-json-cli, immutable-artifact-publication, explicit-output-root, literal-slurm-argv]
key-files:
  created:
    - src/bp_registry/campaigns/cli.py
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-12-TASK-1-RED.json
    - .planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-12-TASK-2-RED.json
  modified:
    - pyproject.toml
    - tests/test_campaign_execution.py
key-decisions:
  - "The lifecycle command accepts JSON only, emits stable JSON envelopes, and preserves all scientific operations in existing campaign modules."
  - "A campaign plan binds the immutable inner-manifest and every assessment target receipt path and hash before any output root is created."
  - "The bounded CLI plan exposes one frozen unit; local and Slurm-shard routes invoke the same canonical unit executor and differ only in their observational route label."
patterns-established:
  - "Validate all input bytes and derived plan identities before creating a campaign output directory."
  - "Use a literal argv for scheduler publication and never evaluate campaign or allocation text as a shell command."
requirements-completed: [LED-05, SIM-01, SIM-02, SIM-03, STAT-01]
coverage:
  - id: D1
    description: Strict lifecycle commands preflight, plan, run locally or as frozen scheduler shard, verify, merge, resume, assess, emit Slurm argv, inspect site capability, and gate measurements.
    requirement: SIM-02
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_cli_lifecycle_uses_preserved_receipts_and_rejects_plan_drift
        status: pass
    human_judgment: false
  - id: D2
    description: Installed command exposes every lifecycle verb and preserves terminal scientific facts across local and scheduler routes.
    requirement: SIM-03
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_installed_cli_exposes_lifecycle_help_and_preserves_route_science
        status: pass
    human_judgment: false
actuals:
  tokens: 8318
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 8ada5a590ce5e7e626157e881d99f2640a240ed1
duration: 5m
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 12: Campaign Lifecycle CLI Summary

**An installed, JSON-only command now drives one frozen campaign through preflight, execution, evidence preservation, reconstruction, and bounded scheduler transport.**

## Accomplishments

- Added `bp-registry-campaign` with strict `preflight`, `plan`, `run-local`, `run-shard`, `emit-slurm`, `merge`, `resume`, `assess`, `verify`, `profile-gate`, and `site-capability` subcommands.
- Validates manifest and target-receipt SHA-256 values, a complete frozen assessment, and derived campaign identities before an execution output root is created.
- Publishes immutable plan and merge JSON; failed or drifted input produces a JSON error and performs no downstream write.
- Uses the existing canonical one-unit executor, shard verifier, fixed-shot reconstructor, Slurm argv builder, and site-capability parser instead of reproducing scientific logic in the CLI.
- Registered the command alongside the existing `bp-registry` study entry point and tested installed local and scheduler routes against the same terminal science.

## Task Commits

1. **Task 1: Provide strict campaign lifecycle subcommands**
   - `46abb36` — RED coverage for a missing preflight command.
   - `2b0a64c` — lifecycle CLI, immutable artifacts, and fail-closed command tests.
2. **Task 2: Install and prove one manifest across local and Slurm routes**
   - `603c1d4` — RED coverage for the absent installed entry point.
   - `5706444` — installed `bp-registry-campaign` script.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'cli and (preflight or plan or lifecycle or malformed or verify)' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_cli or executor_equivalence or resume' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -x` — passed.
- `.venv/bin/python -m compileall -q src/bp_registry/campaigns/cli.py` — passed.
- `git diff --check` — passed.

## TDD Gate Compliance

- Task 1 RED evidence in `08-12-TASK-1-RED.json` returned `RED_EVIDENCE_OK` before the CLI module existed.
- Task 2 RED evidence in `08-12-TASK-2-RED.json` returned `RED_EVIDENCE_OK` before the package entry point existed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Parsed the verified shard campaign specification before reading its assessment digest.**

- **Found during:** Task 1 lifecycle verification.
- **Issue:** Shard verification returns serialized campaign specification data; the CLI initially treated it as a model instance.
- **Fix:** Revalidated the serialized value as `CampaignSpecV1` and returned a JSON error for malformed attribute access.
- **Files modified:** `src/bp_registry/campaigns/cli.py`.
- **Commit:** `2b0a64c`.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed the CLI, entry point, both RED evidence files, and this summary exist.
- Confirmed task commits `46abb36`, `2b0a64c`, `603c1d4`, and `5706444` exist.
- Confirmed `git diff --check` passes and no task-scoped source or test files remain uncommitted.
