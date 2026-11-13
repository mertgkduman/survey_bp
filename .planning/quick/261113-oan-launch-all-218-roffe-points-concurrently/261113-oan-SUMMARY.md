---
status: complete
implementation_status: verified
campaign_status: workers_complete_audit_running
implementation_commit: b121812
---

# Roffe: one CPU for every point

User-authorized dispatch **61785159** contains all **218** frozen points,
**one CPU each**, array concurrency218. It supersedes the old16-point cap and
serial MacKay wait. All218 workers have already finished **COMPLETED,0:0**;
Slurm accounting confirms **AllocCPUS=1 for every task**. Collector **61785160**
is running the unchanged complete-array ledger audit and publisher. Worker
summaries total9,816 retained decoder shots /4,360 failures; these totals are
not presented as independently audited until the collector succeeds.

The original four-CPU MacKay worker **61773602_10** continues. Its pending
advance61781772 remains responsible for completing MacKay's own audits and
publication; it now reuses the existing Roffe array/collector. Actual execution
of the original frozen Roffe --submit after the new launch left dispatch.json
byte-identical, confirming no duplicate jobs. No pending advance was canceled.

Scientific source/grid/code/plan/runner/README files and canonical kernels are
unchanged. Every point uses its existing seed, source min-sum/alpha schedule,
T=n (162/242/338/450), and20 failures/100M stop. The scheduling override is
recorded in LAUNCH-ALL.md and launch-all.json. Frozen plan retains40 pins and
SHA256 eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3.
Old isolation and confirmation plans also load with their unchanged hashes.

Seven targeted execution/source-algorithm tests and Slurm preflight pass.
Shared receipts/lock protect repeated launches and partial-submission recovery.
Final collector requires all218 points; startup/worker completion alone does
not claim audited scientific completion, curve agreement or publication.

This quick dispatch task is complete. Scientific collection/publication remains
running at this snapshot; counts and status are in launch-status.json.
