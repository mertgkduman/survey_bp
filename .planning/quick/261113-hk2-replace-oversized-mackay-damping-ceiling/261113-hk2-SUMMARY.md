---
status: incomplete
implementation_status: verified
campaign_status: running
implementation_commit: 1b040da
---

# Inferred MacKay T=100 budget and replacement tuning

Canceled the oversized damping array **61769653** and its automatic advance
**61769654**. All prior frozen files, 28 completed/16 partial initialized
checkpoints, and the displayed 88,200-iteration curves are preserved. No high
budget damping remains running or pending. STOPPED.json records the cancellation
and retained ledger hashes (33,920 shots / 876 old training failures).

The primary paper's numeric cap remains unspecified in the inspected v3 text,
PDF and TeX source. The user then explicitly authorized inference from curve
alignment. Retrospective first-convergence analysis checked all five source
ledger digests and required only 148 short branch replays (caps <=1,000).
The original bank has 6,284,026 source-arm shots. A 100-per-hypothesis cutoff
minimizes the squared log relative total-error discrepancy among eleven tested
cutoffs: score .0351, versus .0868 at 50 and .1823 at 200. Fifty also fits
reasonably; this does not uniquely recover the historical setting.

| X rate | Retrospective classical rate at 100 | Paper approximate |
| --- | ---: | ---: |
| .010 | 5.686e-6 | 6.699e-6 |
| .013 | 6.617e-5 | 7.075e-5 |
| .020 | .002331 | .002230 |
| .030 | .049784 | .048342 |
| .040 | .175439 | .180784 |

These are calibration counts from an adaptively stopped old bank. Its original
confidence intervals are not transferred. The changing detected-error counts
support the finite-cutoff explanation, without proving that the authors used
100 or excluding other numerical/ordering differences.

Implemented and froze independent replacement studies in `1b040da`:

- **30 fresh baseline points**, seed 2026111317. Ordinary binary BP and joint
  Q-BP each use **T=100**. The source unicycle controller uses **100 per
  hypothesis, at most 200 total**; actual skipped/executed branch work is audited.
  Stop at 20 quantum block failures or 100 million shots. Retain separate
  classical errors and honest source comparison. Old curves stay public.
- **140 T100 damping tuning points**, seven damping values, 1,024 paired fixed
  shots per rate, seed 2026111321. Keep the LER-first selection objective and
  simultaneous paired risk-regret guard before optimizing mean iterations.
- **20–40 fresh T100 confirmation points**, seed 2026111323, selected and
  original settings, 20 failures / 100 million shots. Identical settings run once.
  Training is never pooled into independent confirmation or published as such.
- Successful baseline audit submits T100 tuning, then its complete audit freezes
  confirmation, and its successful audit submits the unchanged **Roffe T=n**
  regular min-sum/Q-BP study. No old canceled chain can launch those stages.

Slurm baseline arrays **61772607** (one CPU), **61772608** (four CPUs) and
**61772609** (16 CPUs) were accepted, with final audit/advance **61772610**.
All **30/30 baseline points** finished and passed the complete ledger audit:
**4,482,325 shots / 600 quantum block failures**. All five length-274 source
ordinates fall inside the fresh, pointwise exact 95% intervals; this is a
descriptive check, not simultaneous reproduction or historical-cap proof.

| X rate | Fresh T100 source rate | Pointwise 95% interval | Paper approximate |
| --- | ---: | --- | ---: |
| .010 | 5.038e-6 | [3.077e-6, 7.474e-6] | 6.699e-6 |
| .013 | 4.974e-5 | [3.038e-5, 7.379e-5] | 7.075e-5 |
| .020 | .002071 | [.001265, .003071] | .002230 |
| .030 | .042827 | [.026353, .062941] | .048342 |
| .040 | .192308 | [.121604, .272981] | .180784 |

T100 tuning array **61773215** and audit **61773216** also completed: **140/140
points, 143,360 fixed training shots / 5,272 failures**, with every actual cap
100. Frozen provisional choices are binary BP d=.85 and Q-BP d=.95 for length
274, and binary BP d=.7 and Q-BP d=.95 for length 74. No speed-based tie was
certified. Independent confirmation has **40 points**, fresh seed 2026111323
and T=100 throughout; array **61773602** and dependent audit/advance **61773603**
are accepted and running/pending. Training cohorts are not public result curves.

Baseline plan: 40 pins, SHA-256
`a60f1906913f5ed2a58281463f7a90436a13ad60d31ce4e1582131428be73b3d`.
T100 tuning plan: 36 pins, SHA-256
`65ba3a1ab1c496efddf948c8cedaa339514242f3a911576808196b3b4845fb42`.
The old large-budget and Roffe plans still load with their original hashes.
No canonical kernel, old frozen scientific file or archived v1 file changed.

Verification: 156 regression checks and 43 final focused checks passed
(overlapping suites). New tests cover cutoff projection versus direct short
runs, short branch/total limits, actual work, real serial/parallel equality and
endpoint audit, independent confirmation caps/seeds, budget incompatibility and
classical/quantum interval separation. Seven public and four short-budget
Chromium workflow groups passed with no page errors. Labels say budget=inferred;
old and new curves coexist, exports agree and stale choices clear. Scheduler
preflight accepted all new worker groups and the new T100 tuning array.

Initial active view: **70 curves / 369 points / 8 codes / 0 circuits**.
The audited baseline adds six separate five-rate curves, for **76 / 399 / 8 / 0**.
A fresh seven-group Chromium run on the measured catalog verifies every public
selector/table/export, empty-result state, stale choices and custom matrix/Stim
workflows, with no page errors. All 147 preexisting raw-catalog series, their
points, and all existing codes/circuits/decoder records compare structurally
identical; none were removed or modified.
Existing catalogs/receipts were preserved. Future checked results use separate
normalized extensions and the shared projection. Concurrent local catalog edits
are preserved with a full refresh snapshot saved under results/catalog.json.

Remaining work: independent confirmation measurements and their automatic complete-ledger audit, then the unchanged Roffe T=n measurements and assessment. Neither retrospective alignment nor
this implementation verification establishes the historical cap or completes
source reproduction. See RESEARCH and the calibration README for the derivation.


## Subsequent results check

All **38 completed confirmation points** passed the full-ledger audit, including
pin/manifest hashes, outcome and work counts, terminal summaries and endpoint
replay: **5,842,388 shots / 760 failures**. Two length-274 Q-BP points at
depolarizing p=.015/.0195 remain running; see the timestamped progress receipt.
The campaign stays incomplete and the Roffe continuation has not yet dispatched.
The held-out comparisons show substantial low-rate LER gains from damping, but
not uniform iteration savings: length-274 Q-BP at p=.060 has unchanged observed
LER and mean iterations 7.109 → 16.2. Frozen choices remain unchanged. Detailed
per-rate original/selected LER and work are in 261113-hk2-RESULTS-CHECK.md.
Partial confirmation results are audited separately and await the planned
complete audit before catalog publication. No new runs or kernel/UI changes
were made during this check.
