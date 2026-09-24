---
phase: quick
plan: 260923-ui8
subsystem: documentation
tags: [matplotlib, pdf, reproducibility, provenance]
requires:
  - phase: 01-evidence-registry-and-native-css-baseline
    provides: Phase 1 documentation and verification evidence
  - phase: 02-canonical-css-execution-and-policy-contracts
    provides: Phase 2 documentation and verification evidence
provides:
  - Deterministic, source-hashed Phase 1--2 PDF documentation snapshot
  - Focused reproducibility and output-safety regression tests
affects: [documentation]
actuals:
  tokens: 132700
  tasks: 2
  commits: 4
plan_head_before: 0cefef76d2d5657de8b3fb3c9e3ec39b6f1c14c0
tech-stack:
  added: []
  patterns: [fixed Markdown inventory, deterministic Matplotlib PDF metadata, atomic local PDF replacement]
key-files:
  created:
    - tools/build_docs_pdf.py
    - docs/policy-bp-documentation-through-phase-2.pdf
    - tests/test_docs_pdf.py
  modified: []
key-decisions:
  - "Render repository Markdown as text with Matplotlib rather than introducing a conversion dependency."
  - "Expose only the fixed approved source inventory through the public renderer API."
requirements-completed: []
coverage:
  - id: D1
    description: Deterministic Phase 1--2 documentation PDF with source SHA-256 provenance and evidence limits.
    verification:
      - kind: unit
        ref: tests/test_docs_pdf.py
        status: pass
      - kind: other
        ref: .venv/bin/python tools/build_docs_pdf.py --output docs/policy-bp-documentation-through-phase-2.pdf --check
        status: pass
    human_judgment: false
status: complete
---

# Quick Task 260923-ui8: Reproducible Phase 1--2 PDF Documentation Summary

**A deterministic Matplotlib PDF snapshot packages the eight approved Phase 1--2 Markdown sources with fixed evidence limits and SHA-256 provenance.**

## Accomplishments

- Added a dependency-free, noninteractive PDF renderer with fixed metadata, fonts, source order, front matter, and atomic sibling-file replacement.
- Checked in `docs/policy-bp-documentation-through-phase-2.pdf`; a fresh `--check` render byte-matches it.
- Added focused tests for determinism, source immutability, evidence labels, PDF structure, fixed inventory, and unsafe input/output paths.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_docs_pdf.py` — 4 passed after the final layout adjustment.
- `.venv/bin/python tools/build_docs_pdf.py --output docs/policy-bp-documentation-through-phase-2.pdf --check` — passed exact byte comparison.
- Protected Markdown, Phase 1/2 verification reports, `.planning/STATE.md`, and `.planning/ROADMAP.md` — no diff.
- Full `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 184 passed in 62.97s after the final permissions fix.
- The generated PDF is 29 pages, has valid PDF header/trailer markers, and is mode 0644 for group readability.

## Task Commits

1. **Task 1: Render the complete Phase 1--2 documentation path into a deterministic PDF** — `53fdcd3` (`feat`)
2. **Task 2: Lock reproducibility, source preservation, and output-path safety** — `7c15906` (`test`)
3. **Final publication fix: Make the PDF shared-readable on this HPC filesystem** — `26dab2a` (`fix`)
4. **Final layout fix: Use short PDF section headings** — `30df961` (`fix`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Render fenced shell commands literally.**
- **Found during:** Task 1
- **Issue:** Matplotlib's default math parsing rejected Markdown code containing shell `$` syntax.
- **Fix:** Disabled math parsing for all rendered text.
- **Files modified:** `tools/build_docs_pdf.py`
- **Verification:** Fresh render and byte-for-byte `--check` pass.
- **Committed in:** `53fdcd3`

**2. [Rule 2 - Safety] Keep the source inventory immutable through the public renderer API.**
- **Found during:** Task 2
- **Issue:** Import callers could provide an alternate source list despite the snapshot's fixed-inventory trust boundary.
- **Fix:** Kept alternate inventory resolution private and made public build/check functions use only `SOURCE_FILES`.
- **Files modified:** `tools/build_docs_pdf.py`, `tests/test_docs_pdf.py`
- **Verification:** Focused tests pass.
- **Committed in:** `7c15906`

**3. [Rule 1 - Bug] Avoid owner-only PDF permissions from `mkstemp`.**
- **Found during:** Final artifact inspection.
- **Issue:** Atomic replacement inherited the temporary file's 0600 mode, preventing collaborators on the shared filesystem from opening the PDF.
- **Fix:** Set the completed temporary PDF to mode 0644 before atomic replacement and assert this in the focused tests.
- **Files modified:** `tools/build_docs_pdf.py`, `tests/test_docs_pdf.py`
- **Verification:** Focused tests, 184-test full suite, and PDF regeneration check pass; resulting artifact mode is 0644.
- **Committed in:** `26dab2a`

**4. [Rule 1 - Layout] Keep long source paths out of large page titles.**
- **Found during:** Final page-geometry inspection.
- **Issue:** Repository-relative verification paths were too long for the large page-title font.
- **Fix:** Use short fixed section titles; retain full paths and digests in the source manifest and smaller running label.
- **Files modified:** `tools/build_docs_pdf.py`, `docs/policy-bp-documentation-through-phase-2.pdf`
- **Verification:** Focused tests and exact PDF regeneration check pass after the final render.
- **Committed in:** `30df961`

## Known Stubs

None.

## Next Phase Readiness

Phase 3 remains not started. This task changed no Markdown source, phase state, roadmap, implementation code, manifest, ledger, or result data.

## Self-Check: PASSED

- `tools/build_docs_pdf.py`, `tests/test_docs_pdf.py`, and `docs/policy-bp-documentation-through-phase-2.pdf` exist.
- Commits `53fdcd3`, `7c15906`, `26dab2a`, and `30df961` exist in the repository history.
