---
status: complete
workflow: gsd-quick
---

# Completed PriorTilt check and OSD runtime explanation

Explained real small-matrix/OSD0 latency regressions, including n162CS10
0.172→0.378ms and n450CS10 .498→.734ms; uniform candidate/winner/digest outputs
remain identical. Versioned provenance/counter/timer overhead is material; no
universal speed-up is claimed and frozen campaigns still use their old code.

Published28/39 full-audited PriorTilt Fig1 pairs (346,440,636 shots/1120 errors):
PriorTilt9/13,Relay10/13,Beam9/13. Four new points include PriorTilt BB70/.0008
(1.694e-7 versus paper1.566e-7) andGB102/.001 (3.847e-7 versus3.637e-7). All28
source ordinates lie within local pointwise95% intervals; all24 previous CSV
rows unchanged. PriorTilt has the lowest estimate at all nine complete
three-method strata, with precision limitations explicit. Figure inspected.

Independent resource reconciliation passes for all five completed parallel
points:13,488 stages/16,951 inherited markers;110,493,696 computed shots split
into109,962,648 retained+531,048 speculative. Parent/resource pins and63 frozen
files unchanged. Eleven ten-CPU point jobs continue (one final audit); BB70
PriorTilt/.0005 hit100M/basis with8/18 errors and stays unpublished until audit.
No worker exception markers, new simulations, production code or software test
reruns; other collectors'16 pre-existing dirty files remain unstaged.

See FINDINGS.md, assessment.json, snapshot-check.json, resource-check.json,
progress snapshots, scheduler captures, publisher/check logs and OSD timing
explanation JSON. Statistical campaign/spike060 remains PARTIAL.
