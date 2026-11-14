---
id: 261114-i9b
status: complete
background_audit: running
implementation_commit: 2c8b6fe
---

# Results checked; full interior audit continues separately

Explained the optimized CS search against the pinned public source. Upstream already factorizes once; its repeated work is modified-syndrome construction and triangular solves per candidate. The qualified uniform-channel implementation instead reuses affine directions, forms pairs with packed XOR, and scores with population counts. Stable signed ordering and complete search coverage remain explicit. The separate compiled BP traversal is excluded from the OSD-only timing claim.

Rebuilt the unmodified native reference with -O3 -march=native, without replacing frozen receipts or the primary environment. All64 selected outputs match; twelve alternating warmed timing rounds on64 source-derived fixtures give2.32–3.53x CS10 ratios. Length450 medians are600.1us native and170.0us optimized. Native returns the selected output with original-syndrome validation; optimized additionally returns full candidates, digest and counters. Constructor/JIT/BP/I/O are excluded. Host conditions and all trials are retained; no exclusive-core, general-matrix or paper-CS60 runtime claim follows. Corrected the old prose about OSD0: length162 was slower; length242 was approximately comparable.

212/218 points have terminal summaries:318,346,784 decoder shots and4,207 logical failures. The fresh check verifies the original frozen plan and every manifest, summary arithmetic, stopping, exact95% intervals, separate stage times/work, complete CS candidate counts, and424 endpoint replays. Every check passes. This does not independently re-read318M interior event rows.

At X-only p=.02, LERs(OSD0,CS10) are(5.280e-5,4.828e-5) on162,(8.868e-6,7.773e-6) on242 and(1.377e-6,1.377e-6) on338. Intervals overlap; these descriptive measurements do not resolve a CS10 advantage there. Damped BP is orders of magnitude worse at the same rate. The paper CS60 values at these three strata lie inside the new pointwise95% intervals. Across all106 completed source strata, CS60 ordinates lie inside97 OSD0 and100 CS10 intervals; different search depth and unavailable author uncertainty preclude treating this as a global reproduction test.

Six points remain running: both methods on338/p=.01,450/p=.01 and450/p=.02. At the recorded check, the four p=.01 points have zero failures after roughly50–77M shots; the450/p=.02 arms have6 and9 failures after21.7M and20.6M shots. These are descriptive progress counters, with no unfinished rates promoted to final estimates.

Full-ledger refresh61820674 runs on one Slurm CPU using the unchanged frozen collector and a private JIT cache. Final complete collector61820676 is serialized behind this refresh and the original array. Retry61805013 already completed0:0; its scheduler dependency record had expired, so final completeness is enforced through retained evidence and the218-point audit. Replaced pending collector61805014; no simulation was canceled or restarted. The interactive interior re-read was stopped before output publication and moved to Slurm. Exact commands/resources are retained.

Saved all109 source-rate comparison rows in COMPARISON.md/comparison-check.csv and212-point evidence in checked-snapshot.json, explicitly labeled summary/endpoint checked. The workbench remains the prior fully audited173-point OSD snapshot:112 curves/1246 points/12 codes/0 circuits, byte-identical to02f802a. Full refresh will update it after the interior audit passes. No canonical, frozen campaign, raw evidence, native source, archivedv1, phase counters or generic Phase7 admission changed. GSD records updated; no new simulations or dependency installations.
