---
status: complete
workflow: gsd-quick
---

# Qualified XYZ production launched

Implemented and froze the exact Table4 BB144/p=.003 XYZ comparison with50 CPUs
per paired decoder point:PriorTilt36060-sweep cap and RelayBP-5 36080-sweep cap,
five converged candidates and stable first minimum original-prior LLR score.
Joint DEMs retain both detector types and all67824/67752 mechanisms; independent
sparse source H/A/priors match. Historical kernels and63 parent frozen files
are unchanged; the relay-list controller is separately versioned.

95 regression cases pass.50-CPU qualification62100693 passes24 matched native
Relay cases plus128 full-budget XYZ events, complete original-DEM evaluation,
all-shot serial candidate/work/trace replay and exact resume. Initial62100295
failed before simulation on inaccessible node-local references; identical pinned
builds are now archived/staged on shared storage with licenses and hashes.

Frozen implementation029786ac and qualified plan3058dfd4 precede dispatch.
Array62102101 tasks0/1 are both RUNNING with50 CPUs/96GiB each;100 initialized
production decoder processes match source-model identities. Collector62102102
is dependency-pending (two reporting CPUs allocated for12GiB). Exact ordered
20-error/100M-shot per-basis stopping, separate speculative work, full fresh
audits and audited-only reports apply. Current production report0/2; pilot and
unfinished estimates excluded. No XYZ paper-agreement claim yet.

See FINDINGS.md, launch-verification.json, qualification-check.json, preservation
checks, tests/launch/freeze logs and scheduler/accounting captures. Production
source/data and usage are in data/reproductions/priortilt-2611-13373-xyz.
Refresh via that study's report.py, not the old XZ publisher. Original XZ is now
39/39 worker-audited with its independent collector61971020 running. No old jobs,
raw evidence, public/v1/catalog files, model configuration or phase gates changed.
Quick launch task is complete; statistical XYZ reproduction remains running.
