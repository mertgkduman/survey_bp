---
phase: quick
plan: 260924-max
subsystem: documentation
tags: [novelty-register, quaternary-bp, relay-bp, pdf]
status: complete
commits: [2a83502]
---

# Cross-kernel memory research question recorded

- Added a provisional entry to `docs/research-novelty-and-depth-register.md` for comparing specified memory/relay effects under separate binary CSS and joint quaternary Pauli BP.
- Distinguished Relay-BP's circuit-level XYZ binary error-mode representation from a four-state Pauli BP kernel, with the distinction labeled as an inference from the primary source.
- Linked the proposed derivation and comparisons to Phases 10–11, with original circuit claims in Phase 13. No quaternary implementation or novelty result is claimed in Phase 4.
- Added `tools/build_novelty_pdf.py` and generated `docs/research-novelty-and-depth-register.pdf` as a current, source-hashed PDF rendering of the living Markdown register. The historical Phase 1–2 documentation PDF was preserved.

## Verification

- `.venv/bin/python tools/build_novelty_pdf.py --check` passed byte-for-byte regeneration.
- `git diff --check` passed for the Markdown and renderer.
- `git diff --exit-code -- docs/policy-bp-documentation-through-phase-2.pdf` confirmed the historical snapshot was unchanged.
- The new artifact was identified as PDF 1.4 by `file`.

## Remaining evidence

The closest-precedent search, four-state memory equations, Y/correlation fixtures, and matched statistical comparisons remain for the later quaternary phases. The register entry is a research question, not an established novelty claim.
