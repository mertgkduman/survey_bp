---
status: incomplete
implementation_status: verified
campaign_status: queued
implementation_commit: ad689b0
---

# Damping tuning and an early BP-OSD baseline

MacKay is complete: 30/30 points, 6,403,005 shots, 600 failures. The final .010
result passed the final automatic collector and portable-receipt/preservation
checks. .010 and .013 are below the approximate paper curve outside local
pointwise 95% intervals; .020/.030/.040 are consistent within individual intervals.
No full source-curve agreement is claimed. Final data commit: `36d3c59`.

Implemented and froze the requested extension in `ad689b0`:

- MacKay ordinary binary SP and joint Q-BP SP on both codes, at all five source
  rates / 1.5x depolarizing rates. Seven damping values, 1,024 paired fixed
  samples per rate: **140 tuning points**, **143,360 planned tuning shots**.
  Each retains the **88,200-iteration ceiling**. Mean LER has first priority;
  mean actual iterations ranks only candidates passing the prespecified paired
  risk-regret guard. All candidate evidence is retained. Training is not public.
- Fresh independent confirmation of selected and original settings, sharing
  equivalent configurations once: **20–40 points**, each stopping at 20 quantum
  block failures or 100 million shots. Source and tuned arms remain separate;
  iterations and directed updates both persist. Selection is provisional;
  the holdout assessment reports measured performance without automatic
  superiority claims.
- Prepared **Roffe et al. 2020, arXiv:2005.07016v2**, an early BP+OSD study with
  explicit regular-BP curves. Its Figure 3 four toric codes use canonical
  **flooding min-sum**, **alpha_t=1-2^-t**, and exactly **T=n**. The exact 109
  plotted baseline rate points (different grids by distance) are extracted and
  checked against error bars. Additional Q-BP min-sum uses the same sweep scale
  and ceiling on matched-marginal depolarizing noise: **218 planned points**.
  No OSD implementation is changed or invoked. Original author ordering/numerics
  are unavailable; source agreement remains to be assessed.

Tuning plan: 34 implementation/artifact/design pins,
`f27b7f62ca0c49f630559f1197a273245eeaf96e396b71a24768383d472a4354`.
Roffe plan: 40 pins,
`eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3`.
Both load and scheduler preflight passed before dispatch. Code/kernel settings
cannot change through a modified plan. Confirmation is frozen after selection
and before its sampling; tuning also pins the next study's implementation/plan.

Slurm tuning array **61769653**, indices 0–139, max 16 one-CPU tasks, is queued
for priority. Dependent advance/audit **61769654** is pending on afterok. Accepted
commands are in `data/reproductions/mackay-0304161-damping/dispatch.json`.
That job requires all tuning ledgers, verifies them and endpoint replays, writes
an immutable selection, freezes confirmation, and submits its array (at most
32 CPUs). Successful confirmation audit publishes its separate normalized
catalog and submits the already-frozen Roffe array (at most 16 CPUs). No Roffe
production jobs have been submitted yet: the requested sequence is enforced.
Failed/missing points prevent advancement. Repeated submits reuse locked receipts.

Verification: 155 regression checks passed; 52 final focused checks passed after
three additional confirmation/pin tests (overlapping suites). Six real development
qualification ledgers / 528 shots passed complete audits and replay, with exact
scientific equality between serial and parallel SP/Q-BP. An independent direct
Algorithm 1 matches the variable-alpha controller. Seven public and five future
Roffe Chromium workflow groups passed, with no page errors. Static identity now
includes alpha_schedule/first_iteration, and labels show the changing scale.

Active public counts remain **70 curves / 369 points / 8 codes / 0 circuits**
before/after new campaign setup. Four newly registered toric inputs are hidden
until eligible measured results exist, including builder/saved choices. Future
confirmed/paper results use the same central retirement/validity/evidence/two-rate
projection; custom matrix/Stim, empty states and archived v1 remain intact.
No kernel or historical frozen evidence is changed. Local raw ledgers and locks
are excluded from Git; portable plans, receipts and future summaries are retained.

Remaining work is Monte Carlo execution, automatic audits/selection/confirmation,
then the Roffe measurements and statistical assessment. Static refresh preserves
local edits, saving a full replacement snapshot under results/catalog.json when
needed. Inspect receipts and scheduler states before calling any stage complete.
