---
status: resolved
trigger: "Investigate why canonical and presentation-adaptation BP4 perform much worse than binary BP on B1 and double-Gross code-capacity depolarizing noise; optimize fairly, then compare with independent BP4 literature."
created: 2026-10-25
updated: 2026-10-25
---

# BP4 performance gap investigation

## Symptoms

- Expected: a four-state BP kernel should exploit X/Z correlation under depolarizing noise and plausibly improve over separate binary BP on matched codes, samples, and iteration budgets.
- Observed: on 100 matched double-Gross shots at p=0.08, the local Q8 tuned BP4 failed 7 versus tuned binary OMS 3; on B1 p=0.10, tuned BP4 failed 40 versus binary 6. Source-slide BP4 rates are much lower.
- Prior checks: physical p-axis reinterpretation does not reconcile all arms; X/Z check updates and graph syndrome semantics match independent four-state parity enumeration.

## Current Focus

- hypothesis: The gap may come from BP4-specific initialization, schedule, clipping, damping, stopping, or code/source policy differences rather than the check parity formula.
- test: Screen a bounded grid on one seed, validate selected settings on held-out matched errors, compare float64 and Q8 BP4 and binary, and benchmark a literature code-capacity BP4 code where code and method are fully specified.
- expecting: Identify a reproducible implementation fault or show a bounded policy-dependent gap with explicit source compatibility limits.
- next_action: retain the presentation reproduction gap as a source-fidelity limitation; proceed with canonical BP4 work using the independently checked kernel

## Evidence

- 2026-10-25: `from_dr_pfister_presentetations/results/pilot_summary.csv` contains initial pilot counts; source transcription is `results/source_curves.csv`.
- 2026-10-25: `.planning/debug/resolved/bp4-css-check-update-audit.md` establishes check-update and syndrome semantics on tiny oracle fixtures.
- 2026-10-25: [Miao et al., IEEE Access 2025](https://publikationen.bibliothek.kit.edu/1000179617/157326592) uses code-capacity depolarizing noise, 25-iteration flooding BP4, and fixed initialization epsilon_0=0.1 by default. Its Figs. 3 and 8 show that BP4 behavior can depend strongly on initialization and code family.
- 2026-10-25: [Kuo and Lai, npj Quantum Information 2022](https://www.nature.com/articles/s41534-022-00623-2) explicitly reports poor conventional BP4 on a highly degenerate GHP code and improvements from MBP4; a blanket BP4-over-BP2 superiority premise is not supported across all codes.
- 2026-10-25: On 10,000 identical Miao toric `[[32,2,4]]` errors at physical p=0.075, prior p0=0.1, and T=25, original author C++ BP4 and the canonical compiled float64 BP4 agreed on every success and syndrome-validity flag: 1,591 failures each. A separate 100-shot run had zero candidate disagreements between public Python and compiled canonical kernels. Local binary OMS failed 3,617/10,000 toric errors. See `from_dr_pfister_presentetations/results/performance_investigation/REPORT.md`.
- 2026-10-25: Fresh double-Gross p=0.08, 3,000 shots: binary OMS 100 failures, slide-like Q8 BP4 185, screened Q8 BP4 with scale 4, damping 0.2, initial p0=0.2 only 79. Paired binary-versus-screened rescues/losses 69/48, exact two-sided p=0.064. The slide tuned BP4 rate 0.00077 remains much lower than 79/3,000.
- 2026-10-25: Fresh B1 p=0.10, 300 shots: binary OMS 13 failures, slide-like Q8 BP4 113, screened Q8 BP4 scale 4/damping 0.4/p0=0.2 failed 42. Canonical float64 BP4 failed 202/300 at p0=0.1 and 145/300 at p0=0.2. The slide tuned BP4 rate 0.00032 remains much lower than 42/300.
- 2026-10-25: Keeping only independent check rows worsened outcomes on matched B1 and double-Gross errors for both binary and BP4. This particular Tanner graph transformation does not explain the presentation gap.

## Eliminated

- A uniform 2/3 physical-p axis shift as a complete explanation.
- An X/Z stabilizer label or check-sign error in the tested implementation.
- A universal canonical BP4 recurrence error, within the independent published toric benchmark tested.
- Q8 quantization alone as the cause of the B1 performance gap; the floating point kernel also performs poorly there.
- Dropping dependent check rows as a remedy on these local code representations.

## Resolution

- root_cause: No general canonical BP4 kernel defect was found. The performance difference is strongly code- and policy-dependent; the exact slide mismatch cannot be uniquely attributed because the presentation omits the executable kernel, Q8 update order, and exact check matrices. The local Q8 adapter is an explicit interpretation of those choices, not source-faithful reproduction.
- fix: No mathematical kernel correction was warranted. Recorded screened local policies separately from presentation policies, retained full matched-shot evidence, pinned and replayed an independent authors' BP4 implementation, and documented the residual source-fidelity limit.
- verification: 10,000 native C++ versus canonical floating-point matched toric outcomes (zero disagreements), 100 public versus compiled canonical candidates (zero disagreements), fresh paired B1/double-Gross confirmation, independent check-row probes, complete ledger recount and hashes, presentation spike checks, and canonical quaternary kernel tests.
- files_changed: `from_dr_pfister_presentetations/` diagnostic runner, audit, policies, literature control, result ledgers/figures/report, and README.
