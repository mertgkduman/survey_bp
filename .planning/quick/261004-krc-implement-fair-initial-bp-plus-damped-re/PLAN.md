---
status: in_progress
quick_id: 261004-krc
date: 2026-10-04
---

# Fair initial BP with damped RelayBP and BeamSearch extensions

## Locked user decision

Replace the next Phase 6 implementation priority with a controlled CSS comparison that starts both decoders from the same initial BP procedure. Count only Relay's subsequent disordered-memory runs as additional Relay legs and BeamSearch's masked/decimated children as additional Beam legs. Run matched damping-off (fresh-message coefficient 1.0) and damping-on (0.5, the user's prior setting) arms; apply the declared setting to both the initial run and every additional unit. Preserve the original paper procedures as separately labeled source configurations.

## Tasks

1. Define a common initial min-sum BP execution and comparable work accounting. Preserve the initial candidate, posterior, V2C messages, iteration count, and convergence decision; stop both methods identically if initial BP succeeds.
2. Implement BeamSearch's masked, warm-started branch expansion, cumulative reliability, ranking, pruning, and source-qualified candidate selection through the existing canonical BP kernel.
3. Implement Relay's extra disordered-memory legs from the same initial posterior; reset messages per leg, transfer posterior only, and keep source-shaped seeded gamma assignments separate from V2C damping.
4. Expose the comparison as a source-qualified, versioned controlled runner with matched samples and a per-shot event ledger, separate initial and extra work, and deterministic replay checks. Add meaningful source and fairness fixtures.
5. Revise Phase 6 planning context to supersede the old AutDEC-first ordering. Run focused and regression tests. Keep the active sealed BB72 v2 run isolated; merge/push only after it is terminal.

## Limits

- Initial BP has identical update, schedule, iteration cap, damping, observation, and seed for both arms.
- A unit after the initial run is a Relay disordered-memory leg or a BeamSearch decimated branch. Record attempted, pruned, successful, and budget-denied units.
- Compare total check-to-variable and variable-to-check work and measured runtime separately; a count of legs alone is not equal compute.
- This BB72 CSS controller is a controlled adaptation, not a circuit-level reproduction of either paper.
