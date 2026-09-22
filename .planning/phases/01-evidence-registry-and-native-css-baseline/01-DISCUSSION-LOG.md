# Phase 1: Evidence Registry and Native CSS Baseline - Discussion Log

> **Audit trail only.** Planning, research, and execution agents should use `01-CONTEXT.md`; this log preserves the choices discussed.

**Date:** 2026-09-21
**Phase:** 1-Evidence Registry and Native CSS Baseline
**Areas discussed:** Initial paper set, Native baseline, Extraction depth, Missing source artifacts

---

## Initial paper set

**User's choice:** BPGD and impulse decoding are priority seed papers. HGP codes in BPGD papers are part of the code inventory.

## Native baseline

| Option | Description | Selected |
|--------|-------------|----------|
| Gross first | Run Gross `[[144,12,12]]` first | |
| B1 first | Run B1 `[[882,24,18≤d≤24]]` first | |
| HGP first | Run an HGP code first | |
| Artifact completeness | Choose whichever has complete, verifiable source artifacts first | ✓ |

**User's choice:** No fixed code order. Include HGP, B1, and Gross family leads; choose the first runnable reference by artifact completeness.

## Extraction depth

| Option | Description | Selected |
|--------|-------------|----------|
| Full source extraction | Capture variant, code/noise settings, reported results, links, and unresolved details | ✓ |
| Core identification | Record verified identity and taxonomy, deepen extraction later | |

**User's choice:** Fully extract CSS code-capacity experiments from the BPGD and impulse papers now. Other decoding regimes remain for later phases.

## Missing source artifacts

| Option | Description | Selected |
|--------|-------------|----------|
| Pilot adaptation | Run a pinned BP reference on verified code inputs and label it an adaptation | ✓ |
| Wait for faithful setup | Offer no native run until original code and exact settings are available | |

**User's choice:** Allow a documented pilot adaptation when source-faithful inputs are unavailable.

## Agent's Discretion

- Choose the exact first code instance, binary BP reference, and practical pilot budget based on verified artifacts and Phase 1 requirements.

## Deferred Ideas

- Full quaternary and circuit experiment extraction, canonical named policies, and statistical curve assessment remain in later phases.
