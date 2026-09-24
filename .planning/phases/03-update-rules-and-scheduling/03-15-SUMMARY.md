---
phase: 03-update-rules-and-scheduling
plan: "15"
subsystem: pilot-evidence-analysis
tags: [notebook, nbclient, matplotlib, retained-evidence, provenance, diagnostics]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: retained matched-pilot ledgers, verified terminals, work vectors, runtime facts, and claim labels
provides:
  - Pinned project-venv execution for the retained-evidence Phase 3 notebook
  - Deterministic pilot outcome/work tables and qualified diagnostic plots
  - Executed notebook metadata without volatile kernel timestamps
affects: [phase-03-verification, css-pilot-analysis, future-reproduction-campaigns]
actuals:
  tokens: 75566
  tasks: 2
  commits: 6
plan_head_before: 3799384643e5508ca9e71c0eda4bd55cf0d096cb
tech-stack:
  added: [matplotlib==3.10.9, nbformat==5.10.4, nbclient==0.10.2, ipykernel==6.29.5]
  patterns:
    - Confined transient kernelspec bound to the project .venv interpreter
    - Read-only ledger/result analysis with durable input digest and trace links
    - Separate full-work, setup-runtime, and decode-runtime reporting without equal-cost claims
key-files:
  created:
    - scripts/execute_phase3_notebook.py
    - notebooks/phase3-pilot-analysis.ipynb
    - data/results/phase3-pilots/phase3-pilot-analysis.executed.ipynb
    - reports/phase3-pilots/outcomes.csv
    - reports/phase3-pilots/work-by-policy.csv
    - reports/phase3-pilots/convergence.png
    - reports/phase3-pilots/work-and-runtime.png
  modified:
    - pyproject.toml
    - tests/test_phase3_pilots.py
key-decisions:
  - "Analysis reads only the retained events.jsonl and result.json inputs; no pilot or decoder execution is invoked."
  - "All output rows and figures retain pilot_adaptation/not_assessed labels, separate setup/decode scopes, missing outcomes, and equal_total_cost_claim=false."
  - "Executed-notebook timing metadata is removed because it is nondeterministic observation noise rather than retained evidence."
requirements-completed: [UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05]
coverage:
  - id: D1
    description: "The source notebook executes through a temporary project-venv kernel under the exact audited analysis pins without running a decoder."
    requirement: UPD-01
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 MPLBACKEND=Agg .venv/bin/python scripts/execute_phase3_notebook.py --input notebooks/phase3-pilot-analysis.ipynb --output data/results/phase3-pilots/phase3-pilot-analysis.executed.ipynb"
        status: pass
    human_judgment: false
  - id: D2
    description: "Retained terminals deterministically produce nonempty outcome/work CSVs and convergence/work-runtime diagnostic PNGs."
    requirement: SCH-02
    verification:
      - kind: integration
        ref: "tests/test_phase3_pilots.py#test_retained_pilot_reports_are_qualified_evidence_without_rankings"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every table preserves missing outcomes, qualified iterations, complete work, separate runtime scopes, trace links, and pilot/adaptation/not-assessed claim limits."
    requirement: SCH-05
    verification:
      - kind: unit
        ref: "tests/test_phase3_pilots.py#test_retained_pilot_reports_are_qualified_evidence_without_rankings"
        status: pass
    human_judgment: false
duration: 11 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 15: Retained Pilot Analysis Summary

**A project-venv notebook now deterministically turns retained Phase 3 pilot evidence into claim-qualified tables and diagnostic plots without rerunning a decoder.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-24T13:29:40Z
- **Completed:** 2026-09-24T13:40:24Z
- **Tasks:** 2/2
- **Files modified:** 9
- **Evidence inputs:** 19 retained terminal records and 95 ledger events.

## Accomplishments

- Added the exact audited `analysis` extra and a confined `nbclient` runner that creates a transient kernelspec beginning with the active project `.venv/bin/python` and forces headless Agg rendering.
- Added a read-only notebook plus executed counterpart that validates retained labels and evidence identities, writes linked outcome/full-work CSVs, and keeps absent outcomes explicit as `unavailable_due_to_stopping`.
- Generated deterministic convergence and work/runtime diagnostics. The reports keep qualified iterations, complete work vectors, trace links, and separate setup/decode timing while explicitly rejecting equal-total-cost, ranking, and reproduction claims.

## Verification

- `OMP_NUM_THREADS=1 MPLBACKEND=Agg .venv/bin/python -m pytest -q tests/test_phase3_pilots.py -k 'notebook or dependency or kernel or report or table or plot or labels'` — 2 passed.
- `OMP_NUM_THREADS=1 MPLBACKEND=Agg .venv/bin/python scripts/execute_phase3_notebook.py --input notebooks/phase3-pilot-analysis.ipynb --output data/results/phase3-pilots/phase3-pilot-analysis.executed.ipynb` — passed.
- Two consecutive notebook executions produced identical SHA-256 values for the executed notebook, both CSVs, and both PNGs.
- `git diff --check 3799384643e5508ca9e71c0eda4bd55cf0d096cb..HEAD` — passed.

## Task Commits

Each task was committed atomically through RED/GREEN checks:

1. **Task 1 RED: notebook execution contract** — `3e63da4` (`test`)
2. **Task 1 GREEN: confined project-kernel notebook execution** — `50d65be` (`feat`)
3. **Task 2 RED: qualified report contract** — `33b49b0` (`test`)
4. **Task 2 GREEN: retained-pilot tables and diagnostics** — `e0fd8f0` (`feat`)
5. **Task 2 correction: portable CSV output** — `c5a8cbd` (`fix`)
6. **Task 2 correction: deterministic executed notebook** — `736579f` (`fix`)

## Files Created/Modified

- `pyproject.toml` — exact optional analysis dependency pins.
- `scripts/execute_phase3_notebook.py` — confined project-kernel execution, exact version checks, and volatile-metadata removal.
- `notebooks/phase3-pilot-analysis.ipynb` — retained-evidence validation and generation of qualified D-18 artifacts.
- `data/results/phase3-pilots/phase3-pilot-analysis.executed.ipynb` — reproducible completed notebook.
- `reports/phase3-pilots/` — evidence-linked CSVs and diagnostic PNGs.
- `tests/test_phase3_pilots.py` — exact-pin, kernel-boundary, artifact, label, missingness, and cost-qualification coverage.

## Decisions Made

- The notebook accepts only expected roots, verifies exact analysis versions, runs the project kernel, and reads retained evidence; it does not call the pilot runner or decoder.
- CSV rows retain `pilot_adaptation`, `not_assessed`, a shared evidence digest, and an event-ledger trace link. Missing outcomes remain missing rather than being inferred.
- Work and timing are diagnostic observations only: complete work vectors and setup/decode scopes remain separate, and equal total cost is explicitly false.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved the project-venv interpreter spelling in the transient kernelspec**
- **Found during:** Task 1
- **Issue:** Resolving the `.venv/bin/python` symlink selected the base interpreter, which could not import the venv-installed `ipykernel`.
- **Fix:** Verify resolved identity for safety but retain active `sys.executable` in the kernelspec argv.
- **Files modified:** `scripts/execute_phase3_notebook.py`, `tests/test_phase3_pilots.py`
- **Verification:** The notebook executed successfully through the project kernel.
- **Committed in:** `50d65be`

**2. [Rule 1 - Bug] Removed nondeterministic report/newline and notebook-timing artifacts**
- **Found during:** Task 2 final integrity checks
- **Issue:** Default CSV CRLF separators failed `git diff --check`, and Jupyter execution timestamps changed across equivalent runs.
- **Fix:** Emit LF CSV records and remove non-evidence execution metadata before writing the executed notebook.
- **Files modified:** `notebooks/phase3-pilot-analysis.ipynb`, `scripts/execute_phase3_notebook.py`, generated CSVs and executed notebook.
- **Verification:** Whitespace check passes; repeated executions have identical hashes for all five generated artifacts.
- **Committed in:** `c5a8cbd`, `736579f`

---

**Total deviations:** 2 auto-fixed Rule 1 correctness issues.
**Impact on plan:** Both changes enforce the plan's exact interpreter and deterministic-output contracts without changing decoder behavior or pilot evidence.

## Issues Encountered

The first `pip install -e '.[analysis]'` exceeded the terminal output window before completion. The same exact audited pins were then confirmed installed in the project environment; no alternative package or version was used.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

Phase 3 has reproducible, claim-safe presentation artifacts for the retained bounded pilots. These diagnostics remain `pilot_adaptation` / `not_assessed`; a source-faithful statistical reproduction campaign still requires its own manifest, tolerance, and compute protocol.

## Self-Check: PASSED

- Confirmed all nine implementation, report, notebook, and test artifacts plus this summary exist.
- Confirmed task commits `3e63da4`, `50d65be`, `33b49b0`, `e0fd8f0`, `c5a8cbd`, and `736579f` are reachable.
- Re-ran the focused notebook/report suite: 2 passed. No stubs, skipped tests, unrun verification, or new network/auth trust surface was introduced.

---
*Phase: 03-update-rules-and-scheduling*
*Plan: 15*
*Completed: 2026-09-24*
