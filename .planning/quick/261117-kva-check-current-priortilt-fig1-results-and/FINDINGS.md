# OSD runtime explanation and PriorTilt result check

“Small-case regressions” means runtime slowdowns on the smaller matrices and
low-cost searches. It does not imply changed candidates or worse logical error
rates on the previously supported uniform settings: complete candidate/winner
and digest equivalence is retained. The label describes matrix/workload size,
not the size of the slowdown.

| Uniform workload | v1 median | v2 fast median | New/old runtime |
|---|---:|---:|---:|
| Toric n162, CS10 |0.171558ms|0.378424ms|2.206x|
| Toric n450, CS10 |0.498104ms|0.734111ms|1.474x|
| LP1054, OSD0 |0.554669ms|0.956724ms|1.725x|
| LP1054, CS10 |2.484597ms|2.143018ms|0.863x|

V2 retains richer versioned input/score/output evidence, typed counters and stage
timing even in fast mode. It computes all candidate/weight digests and a ledger.
On small searches, fixed wrapper/provenance work is a substantial fraction of
latency. The n162 CS10 last-fixture provenance stages have median185.971us in the
sealed benchmark. This is a stage-scope observation, not an additive estimate of
all v1-to-v2 differences. Larger affine searches can offset the extra wrapper
cost. V1 has full materialized candidates but a simpler evidence contract; both
interfaces' scope differences remain explicit. The new version is opt-in and
has not changed the frozen running campaigns.

## PriorTilt Fig1

The resource-aware publisher rehashed saved audited ledgers and shared noise
bindings and refreshed the figure/report:28/39 complete plotted points,
346,440,636 decoded memory-basis shots and1120 observable errors. PriorTilt is
9/13 complete, Relay10/13 and Beam9/13. These are complete X/Z pairs; unfinished
points do not enter published rates.

| Newly published code/rate | Decoder | Local LER/cycle | Paper LER/cycle | Paper inside local95% |
|---|---|---:|---:|---|
|BB70 p=0.0005|relay|7.3107092e-08|8.9868838e-08|True|
|BB70 p=0.0008|priortilt|1.6938319e-07|1.5657799e-07|True|
|GB102 p=0.001|priortilt|3.846802e-07|3.6369822e-07|True|
|GB102 p=0.001|relay|4.4132211e-07|4.86348e-07|True|

All28 source ordinates lie within local pointwise95% intervals; local/source
ratios range0.771–1.253. This is compatibility at local precision, not a
simultaneous full-figure equivalence test. PriorTilt has the lowest point estimate
at all nine completed three-method strata; that does not establish statistically
strict superiority in every stratum. The metric remains the released observable
error convention, (X-memory rate+Z-memory rate)/cycles.

BB70 PriorTilt p=.0005 has reached100M shots for each basis, with8 X-memory and18
Z-memory errors, but awaits its final full audit. It is deliberately absent from
the28-point table. Eleven point jobs remain RUNNING with10 CPUs each (110 CPUs),
including that audit, and collector61971020 remains dependency-pending. No
exception markers were found in the parallel campaign worker logs.

## Verification and preservation

Independent source/count/stopping/CI/work checks pass, including exact equality
of all24 prior complete CSV rows. The final scientific figure was inspected.
The five audited parallel points reconcile13,488 sealed stages and16,951
inherited marker hashes. Computed110,493,696 shots split into109,962,648 retained
and531,048 speculative; all additive work fields and inherited+retained totals
match the canonical ledgers. Speculation remains excluded from LER and retained
work means. Full worker candidate/endpoint audits are preserved.

Parent plan3e466081790d913ae2fb0a477f654bd0218504a79e7d969b989b62043b7e829c
and resource amendmentda570e399be73f21d768d015c124b02fb5ee82796bda498effa284e8ddeb6a22
retain their identities; all63 frozen implementation files are unchanged. No
simulations were submitted or rerun, no production/scoring/kernel code changed,
and software tests were not repeated for this data-only refresh. Other
collectors'16 pre-existing modified outputs remain outside staging.
