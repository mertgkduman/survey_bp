---
phase: quick
plan: 260930-nuv
status: ready
created: 2026-09-30
---

# Quick task: study-design glossary

Create an accessible glossary of the platform's study design as it stands after Phase 5 planning. The deliverables are an editable Markdown source and a reproducible PDF with the same status legend: green = executed at a stated scope, amber = on hold or explicitly cancelled, blue = future/planned. Color is paired with text in both formats.

## Task 1: Author the source-backed glossary

**Files:** `docs/study-design-glossary.md`, `README.md`

**Action:** Define the study regimes, evidence/qualification terms, comparison designs, policies, metrics, and controls using `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, Phase 4 verification/cancellation, and Phase 5 context/research/plans. Provide a status and direct repository source link for each entry. Distinguish completed implementation from pilots, unassessed evidence, held work, and future work. State the as-of date and add a README link to both formats.

**Verify:** Check all glossary source links resolve, every term has one of the three status labels, and Phase 5 is described as planned rather than executed.

## Task 2: Generate and inspect the PDF

**Files:** `tools/build_study_design_glossary_pdf.py`, `docs/study-design-glossary.pdf`

**Action:** Build a deterministic PDF from the Markdown source using the repository's Matplotlib/PdfPages rendering pattern. Render actual colored status bars/cells, accessible text labels, headers, footers, and source provenance. Support `--check` for byte-for-byte regeneration. Review page renders for clipping and readable contrast.

**Verify:** Build, run `--check`, extract PDF text to confirm all terms/statuses, and inspect page previews.

## Task 3: Record and publish

**Files:** `260930-nuv-SUMMARY.md`, `.planning/STATE.md`

**Action:** Record the quick task, commit only the intended documentation/tooling artifacts, and push the current branch to GitHub. Preserve unrelated untracked Phase 4 results.

**Verify:** Confirm the commit and remote branch tip, and report the published branch and files.
