# Verification — pre-dispatch checks pass

Seven targeted checks pass:218 one-CPU array slots, native thread limits,
complete-array collector dependency, receipt idempotence including the frozen
original submitter, partial-submission recovery, no-dispatch preflight, and
unchanged scientific plan/grids/T=n and independent source Algorithm1 agreement.

Slurm --test-only accepted the new array. This is a scheduling feasibility
check, not a completed measurement. Production launch and startup accounting
remain to be verified.

Scientific plan SHA256 remains
`eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3`.
No original Roffe runner, frozen README, source/grid/code/plan file, shared
runtime, canonical kernel, previous receipt or archived interface was edited.


Production launch verified: array61785159, collector61785160, throttle218 and
one CPU/task. Slurm records all218 workers COMPLETED0:0 with AllocCPUS1.
Actual frozen submitter reuse leaves the dispatch receipt byte-identical.
MacKay61773602_10 stays running4 CPUs. No worker error states were found.
Collector remains running; scientific audit/publication is not inferred from
worker completion. New scheduling receipts are distinct from scientific data.
