# PriorTilt Table 4: XYZ joint-DEM reproduction

0/2 paired-memory decoder points passed fresh full worker audits; 50 process workers per point.

Source: [Ye and Delfosse, arXiv:2611.13373v1, Table 4](https://arxiv.org/html/2611.13373v1). BB144 [[144,12,12]], p=.003, 12 cycles. The full joint detector models have 1728 checks and about67800 fault mechanisms per basis.

PriorTilt:60+6000x6=36060 sweeps, source three-phase parameters. RelayBP-5:80+600x60=36080 sweeps, five converged legs including duplicate solutions, first minimum original-prior LLR score. Canonical float64 reduction and indexed randomness differ from the native reference; adaptation rather than bitwise native identity.

Metric=(X-memory observable error rate+Z-memory observable error rate)/12. Nonconvergence is recorded separately. Each basis stops at20 observable errors or100M shots. Local bars are pointwise at-least95% simultaneous X/Z intervals; author precision and1-sigma bars are separate. Qualification and incomplete points are excluded.

| Decoder | X errors/shots | Z errors/shots | Local LER/cycle [95%] | Paper LER/cycle | Paper inside local interval |
|---|---:|---:|---:|---:|---|

No completed local measurements yet. Author measurements are in source-table4.csv.

CSV includes both denominators, failures, nonconvergence, mean all-path sweeps, directed edge updates, random draws, bias updates and instrumented decoder latency per basis. Concurrent50-CPU timing is not a matched single-core or paper-hardware speed comparison. Sampling/evaluation/audit/I/O are outside decoder latency. All sealed speculative work remains separately recorded and fully audited; only ordered exact stopping prefixes enter estimates. Unsealed interrupted work is unmeasured. Publication rehashes bound event chunks and shared samples.
