# PriorTilt Fig. 1 — canonical reproduction campaign

7/39 complete plotted points passed the fresh-process full-ledger audit. Each point uses one CPU for X/Z memories sequentially.

Source: [Ye and Delfosse, arXiv:2611.13373v1](https://arxiv.org/html/2611.13373v1), Fig. 1; exact released circuits, rates and full-precision three-phase schedules. This is a canonical float64 adaptation; native prefix/suffix arithmetic and RNG are separate references.

Local stopping is 20 observable errors or 100 million decoded shots **per memory basis**. The authors use larger counts. Qualification shots and unfinished points are excluded. Nonconvergence is recorded separately, not automatically counted as a logical error. Local bars are at-least-95% simultaneous X/Z bounds; source bars are published 1σ. Agreement is pointwise and limited by local precision.

The CSV retains both denominators, errors, nonconvergence, mean all-path BP sweeps, directed edge updates, random draws, biased-node updates and measured instrumented controller latency per basis. Latency includes trace/provenance and Python admission but excludes sampling, evaluation, audit and I/O; no native runtime comparison is claimed.

| Code | p | Decoder | X errors / shots | Z errors / shots | Local LER/cycle (95%) | Paper LER/cycle | Local/paper | Paper inside local interval |
|---|---:|---|---:|---:|---:|---:|---:|---|
| BB144 | 0.003 | relay | 20/24559 | 20/32816 | 0.0001187 [6.727e-05, 0.0001858] | 0.0001085 | 1.09 | True |
| BB144 | 0.004 | relay | 20/3155 | 20/2746 | 0.001135 [0.0006444, 0.001775] | 0.001118 | 1.02 | True |
| BB144 | 0.004 | beam | 20/2957 | 20/2364 | 0.001269 [0.0007203, 0.001984] | 0.001324 | 0.958 | True |
| BB144 | 0.005 | priortilt | 20/650 | 20/566 | 0.005509 [0.003143, 0.008556] | 0.004395 | 1.25 | True |
| BB144 | 0.005 | relay | 20/315 | 20/393 | 0.009532 [0.005465, 0.01471] | 0.00786 | 1.21 | True |
| BB144 | 0.005 | beam | 20/280 | 20/338 | 0.01088 [0.00625, 0.01676] | 0.01117 | 0.974 | True |
| BB70 | 0.002 | beam | 20/117935 | 20/156889 | 3.301e-05 [1.871e-05, 5.171e-05] | 2.849e-05 | 1.16 | True |

![Source and canonical comparison](comparison.png)

The event ledgers remain under ignored `results/`; audit receipts and their hashes bind the published rows. `run.py --index N --audit` independently reevaluates all original DEM detector and logical equations, reconciles work/lineage and replays chunk endpoints before issuing a receipt. Publication rehashes bound chunks and shared samples.
