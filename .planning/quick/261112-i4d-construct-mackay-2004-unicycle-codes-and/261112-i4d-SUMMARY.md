---
status: complete
implementation_status: verified
campaign_status: complete
implementation_commit: 8e234a4
---

# MacKay Construction U campaign

The foundational-paper follow-up completed all 42 points. Array 61698133
and final collector 61698134 exited COMPLETED (0:0). The final receipt verifies
2,366 shots and 840 block failures, including full ledgers and endpoint replay.
The later paper-rate correction (quick task 261112-k9m) retains these results
as historical evidence and retires the .04–.10 grid from public v2 views.

- Paper: MacKay, Mitchison and McFadden, *Sparse Graph Codes for Quantum
  Error-Correction*, quant-ph/0304161v3 (2004). Primary archive and member
  hashes are pinned in the campaign's `source.json`.
- Codes: [[74,18]] and [[274,110]], with redundant checks and the extra all-one
  column preserved. The length-273 difference-set ordering and paired logical
  bases are project generated and qualified independently.
- Arms: ordinary binary SP, the source's two-hypothesis unicycle SP mechanism,
  and joint Q-BP. X-only rates .04–.10; depolarizing rates .060–.150 at 1.5
  times the X-only rates. Float64, matched priors, Q-BP damping .1, no check cap.
- Budget: 88,200 total sweeps per shot; the two unicycle branches each have a
  44,100 ceiling. Every branch's iterations and both directed message updates
  are counted, including unsuccessful branches. Runtime is retained separately.
- Stop: 20 quantum block failures or 100 million iid shots per point. Type I
  and Type II are retained separately. All logical qubits are evaluated, and
  X/Z signatures cannot cancel. The source's channel and classical error
  plots differ; these are controlled results without a paper-curve claim.
- Slurm: point array **61698133**, dependent audit/publication **61698134**.
  `dispatch.json` records the exact accepted commands; resume is idempotent.
- Final audited portable snapshot: **42/42** terminal points, **2,366** shots
  and **840** block failures. Every point reached 20 failures. Both codes and
  all six curves have their seven rates. Ledger digests, contiguous stopping
  prefixes and first/last-shot replay passed. The earlier 22-point snapshot
  contained 1,697 shots and 440 failures.

The active workbench changes from **64 curves / 339 points / 6 codes / 0
circuits** to **67 curves / 360 points / 7 codes / 0 circuits**. Three complete
seven-rate [[74,18]] curves are added. The single [[274,110]] rate remains
hidden, together with its public input choice, until another measured rate
qualifies a curve. No previous active curve is removed. At full completion the
planned addition is six curves and 42 points, for 70 / 381 / 8 / 0, subject to
the same shared evidence and eligibility rules.

Verification: **136 tests passed** across `tests/research` and the new
construction/campaign tests. After the partial snapshot, **50 focused tests**
passed. Chromium passed **22 workflow groups**: four Construction U groups,
seven public-results groups and eleven curve/plot groups. The new browser
overlay is explicitly synthetic and never written into the evidence catalog.
It checks both matrices, including all 110 logicals, full settings, exports,
adjacent work averages, registered-input validation, saved-controller handling
and removal of stale selections. Existing empty/custom matrix/custom Stim,
mobile and archived v1 checks pass. JavaScript syntax and Git whitespace checks
pass. All 27 frozen implementation/artifact hashes match.

Existing kernels, prior campaigns, raw historical data and the archived v1
interface are unchanged. The data-only normalized catalog extension lets
future rebuilds use the same central active-view rules.

Final collection completed successfully. Before the subsequent paper-rate
retirement, the complete wide-grid view had 70 curves, 381 points, eight codes
and zero circuits. This campaign is scientifically complete under its frozen
controlled settings; it does not establish full agreement with the paper's
curve because its grid overlapped that curve only at p=.04.
