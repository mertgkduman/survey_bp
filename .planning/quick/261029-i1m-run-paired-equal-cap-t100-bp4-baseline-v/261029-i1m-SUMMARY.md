---
status: complete
quick_id: 261029-i1m
date: 2026-10-29
---

# Paired BP4 fairness controls on Yao A5 and B2

Corrected the interpretation of the preceding cross-cap tuned-versus-untuned
comparison. Reused the same pinned codes, physical depolarizing probability
`p=0.06`, compiled canonical BP4 float64 v2 SPA, and independent Type I/II
evaluator. A 20,000-shot paired pilot per arm selected untuned caps close to
the previously selected tuned policies' 100,000-shot mean-iteration targets.
The A5 grid needed a frozen extension to caps 3000/3600/4200. Caps were
frozen at A5 `T=3000` and B2 `T=2400` before the fresh 100,000-shot
evaluation. All 26 tasks and 1,160,000 decoder shots completed; full audit
verified plans, policies, code identities, ledger digests/counts, and shared
physical-error streams.

At equal `T=100`, A5 untuned/tuned failures were 393/186 per 100,000
(2.11× rate reduction), with mean iterations 4.006/3.887 and paired
rescues/losses 224/17. B2 was 255/100 (2.55×), mean iterations
5.779/5.117, rescues/losses 197/42. Both differences were resolved by
two-sided exact paired tests.

At approximately equal mean iterations, A5 untuned/tuned was 178/42 per
100,000 (4.24×), with mean iterations 10.249/9.381 and paired
rescues/losses 140/4. B2 was 27/36, with mean iterations 6.803/6.974;
the reversal was unresolved by a two-sided exact paired test (`p=0.188`).
The work-control means differed by +9.3% on A5 and -2.4% on B2, measured
as untuned relative to tuned. Pilot rates were not used in the evaluation.

The machine-readable plans, policy files, results, counts, exact 90%
intervals, paired tests, PNG/PDF plot, and report are in
`data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/`.
The original tuning README/report and vanilla reproduction README now link
the fair comparison and qualify the earlier 7.5–7.7× cross-cap ratio.
Raw per-shot ledgers remain on the HPC filesystem and are excluded from
Git; manifests/summaries retain their SHA-256 digests.
