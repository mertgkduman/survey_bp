---
status: incomplete
implementation_status: verified
campaign_status: prepared
---

# Roffe: one CPU per point

The user explicitly replaces the16-point concurrency cap and sequential wait
with218 one-CPU tasks. New execution-only launch_all.py uses the original frozen
worker runner, source grids, settings, seeds, T=n and20-failure/100M stop.
The existing MacKay worker continues on4 CPUs. Normal math threads remain1.

The new launcher uses the same lock and array/collect receipt keys as the
original submitter. Thus the old MacKay continuation still performs its own
full audits/publication later, then reuses the existing Roffe jobs. No duplicate
array or premature completion gate is introduced. Final Roffe collector still
requires all218 terminal points before publication.

Seven tests and Slurm preflight pass. Production dispatch/startup remain pending.
No frozen scientific file or canonical implementation changed.
