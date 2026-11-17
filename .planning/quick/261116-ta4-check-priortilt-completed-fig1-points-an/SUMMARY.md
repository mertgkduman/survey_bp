---
id: 261116-ta4
status: complete
campaign_status: running
---

# Fifteen audited Fig1 points agree pointwise with the paper

Initial snapshot: refreshed the unchanged PriorTilt publisher to14/39 completed full-audited decoder/code/rate pairs, containing2,710,989 decoded memory-basis shots and560 observable errors. PriorTilt has4/13 completed points; Relay and Beam each5/13. All14 source ordinates fall inside their corresponding local pointwise95% intervals, with local/paper ratios0.771–1.253. This does not establish simultaneous full-figure agreement. The25 remaining workers continue with one CPU each under61946754; no failures were observed. Collector61946755 remains queued behind the array. The independent-check snapshot records62,748,676 committed shots/714 observable errors including unfinished prefixes, which are retained only as progress counts.

PriorTilt LER/cycle (local versus paper): BB144/0.004 is 0.00064159441 versus 0.00067611136; BB144/0.005 is 0.0055087433 versus 0.0043946995; BB70/0.002 is 1.1636333e-05 versus 1.5085533e-05; GB102/0.002 is 1.9069198e-05 versus 2.0988783e-05. The CSV contains full precision, both denominators and uncertainty. At all four complete three-method strata, PriorTilt has the lowest point estimate. At BB70/.002 its LER is about1.89x lower than Relay and2.84x lower than Beam. Local PriorTilt and Beam intervals there are separated (upper1.823e-5 versus lower1.871e-5); the comparison remains descriptive, at20 observable errors per basis and without multiple-stratum adjustment. Most other method intervals overlap. These are published-setting comparisons, not a matched-latency experiment.

The existing publisher verifies worker full-audit receipts and rehashes every bound event ledger, marker and original shared sample. New `check.py` independently verifies source joins, both denominators, joint logical/convergence counts, exact stopping and intervals, figure aggregation and mean work/latency. All63 frozen file identities remain valid; all seven previously published point records are unchanged. Worker/source/kernel code is unchanged, so the new-data reconciliation was run without repeating already-passing software regression tests. The regenerated three-panel PNG/PDF was inspected. GB102 Relay/Beam have matching terminal sample counts on shared input streams, with distinct policy receipts and different measured work/latency.

The study CSV/report/plot are updated without rerunning simulations or changing stopping, source artifacts, canonical code, previous raw evidence, public catalogs/v1, model configuration or phase gates/counters. Spike060 remains PARTIAL while production continues.

## Late point included before handoff

BB144 PriorTilt at p=.003 completed its audit during this check and is included in the final report. The final snapshot is **15/39 audited points**, comprising five code/rate strata with all three methods, including **5/13 PriorTilt points**, and2,838,888 decoded basis shots/600 observable errors. All15 paper ordinates fall within local pointwise95% intervals. The new point is5.57365e-5 LER/cycle versus5.741e-5 in the paper, interval[3.160e-5,8.731e-5]. PriorTilt has the lowest estimate in all five complete strata. Twenty-four one-CPU workers continue; collector remains pending. `assessment-15.json` preserves the14-point assessment and independently confirms every earlier row is unchanged. The checker accepts an explicit output path so historical snapshots are not overwritten. The final figure was inspected.
