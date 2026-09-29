---
phase: quick
plan: 260929-qaa
type: execute
autonomous: true
mode: inline
must_haves:
  truths:
    - "The dated update reports terminal calibration, exact ledger audit, frozen selections, B1 inconclusiveness, and still-missing fresh evaluation without implying Phase 4 completion."
    - "The PDF is a reproducible rendering of the new Markdown and fixed evidence snapshot."
    - "Only the requested update and its supporting documentation are pushed to GitHub; live campaign bytes remain untouched."
  artifacts:
    - docs/development-update-20260929.md
    - docs/development-update-20260929.pdf
    - docs/evidence/phase4-status-snapshot-20260929.json
    - tools/build_phase4_status_pdf.py
    - README.md
  key_links:
    - "Report claims -> snapshot source hashes -> retained calibration, selection, pilot and native results"
    - "PDF -> exact Markdown and evidence snapshot bytes"
---

# Publish a verified 29 September development update

User request: create a new `.md` and `.pdf` update, then push to GitHub.
Execute inline under the GSD skill's subagent restriction.

## Task 1: Freeze a compact evidence snapshot and write the update

Files: `docs/evidence/phase4-status-snapshot-20260929.json`,
`docs/development-update-20260929.md`, `README.md`.

Action: summarize the terminal calibration and independent audit, selected and
inconclusive settings, completed lower-noise and exact-author diagnostics,
project/phase status, and next gates. Link the update from the README. Preserve
all source identities, counts,
denominators, and claim limits. Do not include raw untracked ledgers in Git.

Verify: recompute source hashes and numerical tables from retained JSON;
check that the snapshot matches the report and all paths exist locally.

## Task 2: Render and publish the PDF

Files: `tools/build_development_pdf.py`, `tools/build_phase4_status_pdf.py`,
`docs/development-update-20260929.pdf`, and quick task metadata.

Action: reuse the existing Matplotlib report renderer with parameterized
header/footer, preserve the old dated PDF bytes, render the new source and
snapshot deterministically, inspect layout, commit only scoped files, and push
the new docs to `origin/main` plus the already isolated audit commit to its
existing branch.

Verify: PDF regeneration check, PDF text/pages, historical PDF hash check,
focused PDF tests, `git diff --check`, and exact remote commit identity.
