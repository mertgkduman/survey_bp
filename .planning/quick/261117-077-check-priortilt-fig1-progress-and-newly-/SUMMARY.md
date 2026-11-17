---
id: 261117-077
status: complete
campaign_status: running
---

# Nineteen audited Fig1 points; PriorTilt remains five complete

The refreshed report contains19/39 full-audited points:5 PriorTilt,7 RelayBP and7 Beam. The completed pairs retain24,299,037 decoded basis shots/760 observable errors. Twenty one-CPU workers continue in array61946754, with no failures reported; collector61946755 remains pending. PriorTilt itself has no newly completed point since the15-point check.

All19 source ordinates fall within the corresponding local pointwise95% intervals. Local/paper ratios remain0.771–1.253. All15 earlier point records are unchanged. PriorTilt still has the lowest measured LER at the five strata where all three methods are complete. The four new source-setting comparisons are:

| Code | p | Method | Local LER/cycle | Paper LER/cycle | Paper inside local95% |
|---|---:|---|---:|---:|---|
| BB144 | 0.002 | relay | 5.8078e-06 | 5.49529e-06 | True |
| BB144 | 0.002 | beam | 4.28948e-06 | 5.44117e-06 | True |
| BB70 | 0.001 | relay | 9.80082e-07 | 1.11309e-06 | True |
| BB70 | 0.001 | beam | 1.08051e-06 | 9.80952e-07 | True |

The saved progress snapshot shows BB144 PriorTilt/p=.002 at778,240/770,048 X/Z shots with10/13 errors, and BB70 PriorTilt/p=.001 at5,029,888/5,021,696 shots with10/12 errors. These are unfinished counts, not rates or bounds. Every basis continues toward20 observable errors or100M decoded shots. The later independent-check snapshot records171,550,237 total committed shots/906 observable errors including unfinished prefixes. No stopping or budget was changed.

The unchanged publisher verifies worker full-ledger receipts and rehashes all bound committed candidate chunks/markers/shared original samples. The independent checker verifies source joins, both denominators, convergence/error joint counts, stopping intervals, figure aggregation, mean work/timing, receipt hashes and preservation of the previous15 points. All63 frozen identities remain valid. The three-panel PNG/PDF was inspected. An early check ran against the previous15-point CSV while publication was still hashing the new evidence; its passing receipt is retained as `assessment-before-refresh.json`. The final19-point receipt is `assessment.json`. No old assessment was overwritten.

No software changed, so already-passing software regressions were not repeated for this data-only update. No simulations were rerun and no source/frozen/kernel/public/v1/model/phase gates or counters changed. Spike060 remains PARTIAL while the campaign continues.
