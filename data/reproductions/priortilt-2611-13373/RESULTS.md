# PriorTilt Fig. 1 — canonical reproduction campaign

39/39 complete plotted points passed the fresh-process full-ledger audit. The original workers used one CPU; remaining points continue under the ten-CPU resource amendment, sharing one process pool across the X/Z memory runs.

Source: [Ye and Delfosse, arXiv:2611.13373v1](https://arxiv.org/html/2611.13373v1), Fig. 1; exact released circuits, rates and full-precision three-phase schedules. This is a canonical float64 adaptation; native prefix/suffix arithmetic and RNG are separate references.

Local stopping is 20 observable errors or 100 million decoded shots **per memory basis**. The authors use larger counts. Qualification shots and unfinished points are excluded. Nonconvergence is recorded separately, not automatically counted as a logical error. Local bars are at-least-95% simultaneous X/Z bounds; source bars are published 1σ. Agreement is pointwise and limited by local precision.

The CSV retains both denominators, errors, nonconvergence, mean all-path BP sweeps, directed edge updates, random draws, biased-node updates and measured instrumented controller latency per basis. Latency includes trace/provenance and Python admission but excludes sampling, evaluation, audit and I/O; no native runtime comparison is claimed.

| Code | p | Decoder | X errors / shots | Z errors / shots | Local LER/cycle (95%) | Paper LER/cycle | Local/paper | Paper inside local interval |
|---|---:|---|---:|---:|---:|---:|---:|---|
| BB144 | 0.001 | priortilt | 19/100000000 | 16/100000000 | 2.917e-08 [1.583e-08, 4.907e-08] | 2.082e-08 | 1.4 | True |
| BB144 | 0.001 | relay | 20/37143730 | 20/41669172 | 8.487e-08 [4.811e-08, 1.33e-07] | 8.967e-08 | 0.946 | True |
| BB144 | 0.001 | beam | 20/53664836 | 20/68213472 | 5.549e-08 [3.146e-08, 8.693e-08] | 6.5e-08 | 0.854 | True |
| BB144 | 0.002 | priortilt | 20/1256803 | 20/1192846 | 2.723e-06 [1.544e-06, 4.266e-06] | 2.467e-06 | 1.1 | True |
| BB144 | 0.002 | relay | 20/719387 | 20/477417 | 5.808e-06 [3.293e-06, 9.099e-06] | 5.495e-06 | 1.06 | True |
| BB144 | 0.002 | beam | 20/690348 | 20/888778 | 4.289e-06 [2.432e-06, 6.72e-06] | 5.441e-06 | 0.788 | True |
| BB144 | 0.003 | priortilt | 20/47671 | 20/80228 | 5.574e-05 [3.16e-05, 8.731e-05] | 5.741e-05 | 0.971 | True |
| BB144 | 0.003 | relay | 20/24559 | 20/32816 | 0.0001187 [6.727e-05, 0.0001858] | 0.0001085 | 1.09 | True |
| BB144 | 0.003 | beam | 20/21287 | 20/31527 | 0.0001312 [7.437e-05, 0.0002054] | 0.0001101 | 1.19 | True |
| BB144 | 0.004 | priortilt | 20/4737 | 20/5752 | 0.0006416 [0.000364, 0.001004] | 0.0006761 | 0.949 | True |
| BB144 | 0.004 | relay | 20/3155 | 20/2746 | 0.001135 [0.0006444, 0.001775] | 0.001118 | 1.02 | True |
| BB144 | 0.004 | beam | 20/2957 | 20/2364 | 0.001269 [0.0007203, 0.001984] | 0.001324 | 0.958 | True |
| BB144 | 0.005 | priortilt | 20/650 | 20/566 | 0.005509 [0.003143, 0.008556] | 0.004395 | 1.25 | True |
| BB144 | 0.005 | relay | 20/315 | 20/393 | 0.009532 [0.005465, 0.01471] | 0.00786 | 1.21 | True |
| BB144 | 0.005 | beam | 20/280 | 20/338 | 0.01088 [0.00625, 0.01676] | 0.01117 | 0.974 | True |
| BB70 | 0.0005 | priortilt | 8/100000000 | 18/100000000 | 2.889e-08 [1.431e-08, 5.232e-08] | 2.543e-08 | 1.14 | True |
| BB70 | 0.0005 | relay | 20/62610970 | 20/59078786 | 7.311e-08 [4.145e-08, 1.145e-07] | 8.987e-08 | 0.813 | True |
| BB70 | 0.0005 | beam | 18/100000000 | 20/41011040 | 7.419e-08 [4.167e-08, 1.183e-07] | 6.972e-08 | 1.06 | True |
| BB70 | 0.0008 | priortilt | 20/50216098 | 20/17759307 | 1.694e-07 [9.603e-08, 2.654e-07] | 1.566e-07 | 1.08 | True |
| BB70 | 0.0008 | relay | 20/13234136 | 20/8569842 | 4.272e-07 [2.422e-07, 6.693e-07] | 4.817e-07 | 0.887 | True |
| BB70 | 0.0008 | beam | 20/16307665 | 20/9612294 | 3.675e-07 [2.083e-07, 5.757e-07] | 3.764e-07 | 0.976 | True |
| BB70 | 0.001 | priortilt | 20/13566669 | 20/9577053 | 3.958e-07 [2.244e-07, 6.201e-07] | 4.678e-07 | 0.846 | True |
| BB70 | 0.001 | relay | 20/4405117 | 20/4672283 | 9.801e-07 [5.556e-07, 1.535e-06] | 1.113e-06 | 0.881 | True |
| BB70 | 0.001 | beam | 20/6624128 | 20/2982691 | 1.081e-06 [6.126e-07, 1.693e-06] | 9.81e-07 | 1.1 | True |
| BB70 | 0.002 | priortilt | 20/398510 | 20/366703 | 1.164e-05 [6.597e-06, 1.823e-05] | 1.509e-05 | 0.771 | True |
| BB70 | 0.002 | relay | 20/170875 | 20/248101 | 2.196e-05 [1.245e-05, 3.441e-05] | 2.428e-05 | 0.904 | True |
| BB70 | 0.002 | beam | 20/117935 | 20/156889 | 3.301e-05 [1.871e-05, 5.171e-05] | 2.849e-05 | 1.16 | True |
| GB102 | 0.0005 | priortilt | 6/100000000 | 5/100000000 | 1.222e-08 [3.589e-09, 2.997e-08] | 1.167e-08 | 1.05 | True |
| GB102 | 0.0005 | relay | 9/100000000 | 8/100000000 | 1.889e-08 [7.41e-09, 3.933e-08] | 1.511e-08 | 1.25 | True |
| GB102 | 0.0005 | beam | 7/100000000 | 6/100000000 | 1.444e-08 [4.792e-09, 3.315e-08] | 2.306e-08 | 0.627 | True |
| GB102 | 0.0008 | priortilt | 20/33064976 | 20/35932181 | 1.291e-07 [7.316e-08, 2.022e-07] | 1.124e-07 | 1.15 | True |
| GB102 | 0.0008 | relay | 20/25499672 | 20/35250303 | 1.502e-07 [8.514e-08, 2.353e-07] | 1.76e-07 | 0.853 | True |
| GB102 | 0.0008 | beam | 20/21541473 | 20/22323309 | 2.027e-07 [1.149e-07, 3.176e-07] | 1.911e-07 | 1.06 | True |
| GB102 | 0.001 | priortilt | 20/10442982 | 20/12928582 | 3.847e-07 [2.181e-07, 6.026e-07] | 3.637e-07 | 1.06 | True |
| GB102 | 0.001 | relay | 20/8178778 | 20/13101473 | 4.413e-07 [2.502e-07, 6.914e-07] | 4.863e-07 | 0.907 | True |
| GB102 | 0.001 | beam | 20/7643051 | 20/6864264 | 6.145e-07 [3.484e-07, 9.627e-07] | 5.8e-07 | 1.06 | True |
| GB102 | 0.002 | priortilt | 20/199810 | 20/279612 | 1.907e-05 [1.081e-05, 2.987e-05] | 2.099e-05 | 0.909 | True |
| GB102 | 0.002 | relay | 20/156698 | 20/162358 | 2.787e-05 [1.58e-05, 4.366e-05] | 2.455e-05 | 1.14 | True |
| GB102 | 0.002 | beam | 20/156698 | 20/162358 | 2.787e-05 [1.58e-05, 4.366e-05] | 2.86e-05 | 0.974 | True |

![Source and canonical comparison](comparison.png)

The event ledgers remain under ignored `results/`; audit receipts and their hashes bind the published rows. `run.py --index N --audit` independently reevaluates all original DEM detector and logical equations, reconciles work/lineage and replays chunk endpoints before issuing a receipt. Publication rehashes bound chunks and shared samples.

Resource history: `resource-amendment.json` binds the unchanged scientific plan to `parallel.py` and ten CPUs per remaining point. Original prefixes are preserved. Sealed batches may compute ahead; only the exact ordered stopping prefix enters this table. Extra work is retained separately in each point's `parallel-work.json`, with all sealed speculative candidates independently audited. Original single-CPU and concurrent ten-CPU timing cohorts should be analyzed separately; pooled mean decoder time is not a standalone single-CPU benchmark. Interrupted work before a sealed stage has no measured counter.
