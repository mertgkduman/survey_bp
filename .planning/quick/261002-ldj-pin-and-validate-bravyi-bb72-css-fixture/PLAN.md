---
status: in_progress
quick_id: 261002-ldj
date: 2026-10-02
---

# Pin and validate Bravyi BB72 CSS fixture

## Goal

Provide an immutable [[72,12,6]] bivariate bicycle CSS artifact suitable for a small-code controlled BP comparison, with exact source construction and independently checked algebra. This fixture is not a source-paper decoder reproduction.

## Tasks

1. Read the pinned Bravyi source comment for the [[72,12,6]] parameters and require the same reviewed Hx/Hz construction shape as the BB144 freeze tool.
2. Generate deterministic Hx/Hz and project-derived paired Lx/Lz, with source revision and artifact hashes in a provenance sidecar.
3. Verify CSS commutation, ranks, k, logical commutation and independent parsing, then add a public manifest fixture and focused test.
4. Commit implementation and record the fixture limitation in the summary.
