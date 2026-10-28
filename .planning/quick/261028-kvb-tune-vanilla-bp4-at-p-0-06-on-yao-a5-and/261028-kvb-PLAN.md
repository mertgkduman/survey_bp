---
status: complete
quick_id: 261028-kvb
date: 2026-10-28
description: Tune canonical BP4 at physical p=0.06 on the pinned Yao A5 and B2 codes with paired screening, independent validation, and a 90% stopping rule.
---

# BP4 tuning on A5 and B2

1. Reuse the frozen A5/B2 code identities, depolarizing sampler, and independent block-failure classifier. Pin a strict data-only candidate registry; record numerical profile, check rule, message resolution, decoder prior p0, V2C damping, check cap, and iteration limit. Keep original vanilla BP4 v2 as the baseline.
2. On a screening seed for each code, stop the baseline after six block failures (bounded by 10,000 shots). Evaluate every candidate on precisely that fixed paired shot prefix. This is exploratory screening, not an unbiased rate estimate.
3. Use an independent seed and larger fixed paired samples to compare promising candidates and refine the best neighborhood. Freeze a small finalist set before independent validation.
4. Stop when no tested neighboring parameter setting moves the estimated block-failure rate outside the incumbent's exact 90% interval and no paired comparison supports an improvement at 90% confidence. State the finite tested neighborhood and uncertainty limit; do not claim a global optimum.
5. Save per-shot ledgers, manifests, comparison tables, selected decoder files, plots, and clear replay instructions. Verify code identities, sample pairing, outcome classes, hashes, and focused tests. Commit the completed GSD quick task.

## Cap-tail stopping clarification (recorded before the long-cap runs finished)

With first-valid stopping, increasing only `T` cannot worsen a shot that already converged. An exact paired McNemar test can therefore detect a very small one-way gain even when its rate effect is far inside the incumbent's 90% LER interval; using that test alone would drive an unbounded cap search. Once a larger cap triggers the initial follow-up, judge practical cap saturation by an exact one-sided 90% upper bound on its rescue probability. Stop the finite cap search when this upper bound is smaller than the incumbent's observed LER minus its exact two-sided 90% lower limit, and the larger-cap point estimate remains inside that interval. Continue to report all paired rescue counts and p-values. For damping and decoder-prior changes, retain the paired comparison as a distinct diagnostic; do not call the finite search a global optimum.
