---
id: 261117-exr
status: complete
campaign_status: running
---

# Two new PriorTilt measurements;23 audited campaign points

The updated report contains23/39 full-audited points:7/13 PriorTilt and8/13 each RelayBP/Beam, retaining97,616,345 decoded memory-basis shots and920 observable errors. Sixteen one-CPU workers continue in61946754, without reported failures; collector61946755 remains pending. All23 paper ordinates lie within their local pointwise95% intervals, local/paper ratios0.771–1.253. All19 previously checked point records are unchanged. PriorTilt has the lowest point estimate at all seven complete three-method strata. This remains a precision-limited pointwise comparison at published settings, not a simultaneous curve or matched-latency claim.

Four new completed comparisons:

| Code | p | Method | Local LER/cycle | Paper LER/cycle | Local95% interval |
|---|---:|---|---:|---:|---|
| BB144 | 0.002 | priortilt | 2.723335e-06 | 2.466731e-06 | [1.543903e-06, 4.266412e-06] |
| BB70 | 0.0008 | relay | 4.272232e-07 | 4.816781e-07 | [2.421991e-07, 6.692959e-07] |
| BB70 | 0.0008 | beam | 3.67454e-07 | 3.763889e-07 | [2.083151e-07, 5.756604e-07] |
| BB70 | 0.001 | priortilt | 3.958363e-07 | 4.677876e-07 | [2.244054e-07, 6.201246e-07] |

The new BB144 PriorTilt/p=.002 pair has20/1,256,803 X-memory and20/1,192,846 Z-memory errors/shots. BB70/p=.001 has20/13,566,669 and20/9,577,053. The other two new points are Relay/Beam at BB70/p=.0008. The independent-check progress snapshot totals479,428,132 committed decoder-basis shots/1,119 observable errors, including unfinished prefixes. These progress counts are not provisional rates or bounds. Rare points remain at20-error/100M-shot stops per memory basis, with X/Z sequentially handled on each worker's one CPU.

The unchanged publisher rehashes every bound candidate chunk, marker and original shared sample and verifies full-worker-audit receipts. Independent source joins, denominators, joint logical/convergence counts, stopping/interval arithmetic, figure aggregation, mean work/latency, receipt hashes and all19 earlier points reconcile. All63 frozen identities remain valid. The regenerated three-panel PNG/PDF was inspected. Production code is unchanged, so already-passing software regressions were not repeated for the data-only refresh.

Sixteen files from other completed collectors (LP/gamma/OSD/public-catalog outputs) were already modified at entry. This check leaves those files outside its staged scope. No simulations, kernels, frozen/source artifacts, old evidence, public/v1/model configuration or phase gates/counters were changed by this task. Spike060 remains PARTIAL while production continues.
