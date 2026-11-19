---
status: complete
workflow: gsd-quick
---

Tune the BP sweeps inside the frozen PriorTilt, RelayBP and BeamSearch
controllers. Use BB144 p=.003 and BB70/GB102 p=.001 on the released XZ
circuits. Include existing BB144 XYZ PriorTilt and RelayBP-5 at p=.003.
Keep original controller schedules, work budgets, candidate/fallback logic,
and the released detector and observable model.

Use V2C damping first, then check scaling and offset around the best damping
settings. Screen on syndromes where independent 40-sweep ordinary BP does
not converge at the requested physical rates. Keep the same samples and
policy seeds across candidates in each round and record the conditioning.
Rank by observable errors, then directed edge work for near ties. Retain
neutral controls across stages. Confirm the selected configuration with
unfiltered, independent evaluation shots using the existing 20-error/100M
per-memory stopping rule.

Qualify neutral and non-neutral controls, original budget/fallback/trace
semantics, protected numerical range and the spawned Slurm paths. Freeze
a separate study and submit 20 CPUs per point with scheduler dependencies.
