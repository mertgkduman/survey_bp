---
phase: quick
plan: 260930-nuv
status: complete
completed: 2026-09-30
mode: inline
implementation_commit: 6ddf013
---

# Study-design glossary in Markdown and PDF

Created `docs/study-design-glossary.md` and its seven-page color-coded PDF. The glossary has 57 status-labeled entries across the study sequence and definitions. Green means executed at the stated scope, amber means on hold/cancelled/inconclusive, and blue means future or planned. Every status has a text label; the Markdown includes 64 working repository links. The PDF has a source digest and an index of the cited files. `README.md` links both formats.

The source snapshot distinguishes completed Phases 1–4 from the verified but unexecuted Phase 5 plans. It keeps the cancelled Phase 4 comprehensive evaluation and inconclusive B1 Relay selection explicit; it does not claim a publication-curve reproduction or decoder ranking.

Validation: all Markdown links resolve, all glossary rows have an allowed status, the PDF rebuilds byte-for-byte with `--check`, and all seven rendered pages were visually inspected. `git diff --check` passed. The changed files were staged explicitly; unrelated untracked Phase 4 results were not included.

Publication target: `origin/gsd/phase-01-evidence-registry-native-css`, matching the current local branch. GitHub `main` is left at its existing tip because the local branch also contains 80 prior unpublished commits.
