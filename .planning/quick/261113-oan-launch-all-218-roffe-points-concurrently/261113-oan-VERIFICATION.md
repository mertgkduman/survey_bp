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
