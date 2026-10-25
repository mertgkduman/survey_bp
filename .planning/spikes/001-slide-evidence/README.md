---
spike: 001
idea: pfister-slide-bp-reproduction
name: slide-evidence
type: standard
validates: "Given the supplied slides, when data and policies are transcribed, then every curve point and setting is attributable"
verdict: VALIDATED
related: [002-policy-kernel, 003-paired-reproduction]
tags: [provenance, policies]
---

# Spike 001: Slide evidence

## What This Validates

The user-supplied TikZ point tables, decoder knobs, and numerical claims can be stored as explicit source evidence without implying that a local simulation measured them.

## Research

The slide excerpt itself is the source for decoder settings and plotted values. The double-Gross `[[288,12,18]]` `(12,12)` polynomial pair is supported by [Bravyi et al.](https://arxiv.org/abs/2308.07915) and [a follow-up construction table](https://arxiv.org/pdf/2407.16336). The project's frozen B1 construction is `src/bp_registry/code_constructions.py`.

## How to Run

`.venv/bin/python from_dr_pfister_presentetations/plot_results.py`

## What to Expect

`results/source_curves.csv` has 41 source points and `plots/source_curves.png` rebuilds the two presented LER curves. The double-Gross `p=0.06` tuned BP4 point is explicitly a 95% one-sided upper bound for zero failures in 100,000 trials.

## Investigation Trail

1. Transcribed all visible numeric TikZ coordinates and the four decoder settings.
2. Retained the double-Gross `p=0.04` point even though it is below the slide plot's lower y-limit.
3. Kept unknown denominators blank; only the exact zero-failure bound reveals a denominator.
4. Recomputed ratios: 16.875, 470.42, and 4.286, agreeing with the rounded slide claims.
5. Recorded damping, quantization, MBP, and iteration-limit statements without inventing missing figure values.

## Results

**VALIDATED.** Seven policy/screen files, 41 source points, source claims, and the source plot are under `from_dr_pfister_presentetations/`. `verify_spike.py` checks the point count and zero-failure bound.
