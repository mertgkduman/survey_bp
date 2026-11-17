---
id: 261116-rf9
status: complete
campaign_status: running
---

# PriorTilt snapshot checked; OSD-CS speedup scope reconfirmed

Published7/39 complete full-audited paired-memory points from the unchanged frozen PriorTilt Fig1 campaign. These contain345,963 decoded basis shots and280 observable errors (20 per X/Z basis). All seven published paper ordinates fall within the corresponding local pointwise95% intervals; local/paper ratios range0.958–1.253. This is a precision-limited pointwise observation, not simultaneous agreement of the full figure or native bitwise identity. Thirty-two one-CPU workers continue under61946754; dependent collector61946755 remains pending. The later progress check retained13,863,054 committed shots/452 observable errors across all39 workers; unfinished prefixes are not published as rates or bounds.

At BB144/p=.005, LER/cycle is .005509 for PriorTilt (paper .004395), .009532 for RelayBP (.007860), and .010881 for Beam (.011171). PriorTilt's point estimate is lower, while local intervals overlap. The other completed points are Relay at BB144/.003 and .004, Beam at BB144/.004, and Beam at BB70/.002. Full counts, intervals and mean work/latency remain in the study CSV. Source and canonical uncertainty bars are distinct. The three-panel image was inspected.

The existing collector rehashes every bound committed candidate ledger, marker and shared original sample before publishing each worker's full-audit receipt. New `check.py` independently recomputes the source join, both denominators, joint logical/convergence counts, exact stopping intervals, figure metric and mean work/timing, and verifies every CSV receipt hash. Frozen63-file plan identity remains valid. Thirteen affected runtime/audit/report regressions pass. No production simulation, native benchmark or earlier campaign was rerun.

OSD explanation was checked against current `postprocessing/osd.py`, the pinned native C++ `osd.hpp`, and the immutable261114-i9b host-target benchmark. The implementation hash still matches. Upstream already factorizes once per decode; it then constructs a modified syndrome and triangular-solves each trial. Our uniform-channel CS implementation precomputes affine flip directions once, forms pair candidates with packed uint64 XOR and scores with population counts, using compiled contiguous loops. The candidate search and first-minimum rule are retained, supported by404 complete source/oracle comparisons. The new check confirms the existing warm standalone **CS10 versus CS10** ratios2.32–3.53x with native `-O3 -march=native`; length450 is600.1us versus170.0us. These exclude BP, construction/JIT and ledger I/O and apply to the qualified uniform binary small-toric regime. No universal OSD0, general nonuniform-circuit or paper-CS60/full-decoder runtime claim follows.

Prior GSD spike060 remains PARTIAL while the39-point experiment finishes. Source/controller qualification remains unchanged. No canonical/frozen code, raw data, source artifacts, public catalog, archivedv1, model configuration or phase gates/counters changed.
