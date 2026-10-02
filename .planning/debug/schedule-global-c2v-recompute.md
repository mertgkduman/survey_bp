---
status: resolved
trigger: "Independent correctness audit found layered and serial BP schedules recompute whole-graph C2V messages at local update steps while charging only local work."
created: 2026-10-02
updated: 2026-10-02
---

# Symptoms

- Expected behavior: Layered, check-node serial, and variable-node serial schedules update only their declared local unit according to source semantics and charge all actual C2V operations.
- Actual behavior: `LayeredSchedule._compute_layer`, `CheckNodeSerialSchedule._compute_unit`, and `VariableNodeSerialSchedule._compute_unit` call `_all_c2v` on the full graph from mixed-age V2C state at each local step; unselected messages can change without declared work.
- Error messages: None; this is a semantic and accounting discrepancy.
- Timeline: Found in independent audit of current Phase-3 schedules on 2026-10-02.
- Reproduction: Inspect `src/bp_registry/canonical/schedules.py` around lines 341-360, 643-652, and 707-723; compare work vectors and message state on a small graph with two or more units.

## Current Focus

- hypothesis: Whole-graph C2V recomputation is erroneously used for local schedule updates.
- test: Build a small independent fixture where a prior local update changes incoming V2C for an unselected check; compare state and counted work.
- expecting: Current state changes nonselected C2V or uses uncharged recomputations; corrected local update leaves them unchanged until selected.
- next_action: resolved; commit the focused correction after the regression suite passes

## Evidence

- timestamp: 2026-10-02
  observation: `LayeredSchedule._compute_layer` calls `_all_c2v` before redoing only the selected layer (`schedules.py:349-366`); `CheckNodeSerialSchedule` and `VariableNodeSerialSchedule` do the equivalent at `:643-652` and `:707-723`.
  implication: Every local unit evaluates all C2V edges from the current V2C state, although Layered and CN work vectors charge selected edges only and VN charges zero C2V edges.
- timestamp: 2026-10-02
  observation: The public execution and independent verifier construct a fresh local schedule per shot/attempt (`execution.py:1097-1110`; `verification.py:522-526`), so an instance-owned buffer is attempt-local in production.
  implication: A local C2V buffer can preserve selected messages between local units without extending the public manifest or ledger contract.
- timestamp: 2026-10-02
  observation: Local and residual execution bounded `range(max_iterations)` by local commits, while `ScheduleProgress.iteration` advances only after a complete layered/node-serial/randomized traversal or residual edge traversal.
  implication: A public limit of one had been stopping at one local unit rather than one source iteration.
- timestamp: 2026-10-02
  observation: Randomized plans declared configuration, attempt, or sweep order-refresh scopes, but the executor and independent replay always asked to refresh at `attempt` for every local unit.
  implication: Configuration scope failed at runtime and sweep scope could redraw within one declared traversal.

## Eliminated

## Resolution

- root_cause: Local schedule helpers treated C2V as an ephemeral full-graph derivative of V2C, even though local C2V age is mutable schedule state. The two orchestration loops similarly treated their local-unit counters as source-iteration counters.
- fix: Added an attempt-local C2V cache to layered and node-serial schedules; a committed unit now recomputes only its selected canonical edges and commits that cache only after admission. Variable-node serial reserves its incident C2V operations. Execution and independent replay now run complete source traversals for layered, node-serial, randomized, and residual schedules; Hsu group scheduling retains its documented local-group limit. Randomized orders are admitted at configuration/attempt start or each sweep according to the declared scope and reused through the traversal.
- verification: `tests/canonical/test_schedule_semantics.py` (23 passed), `tests/canonical/test_residual_schedule.py` (10 passed), `tests/canonical/test_local_memory_execution.py` (22 passed), `tests/test_manifest.py -k 'check_node_serial or variable_node_serial or residual or randomized'` (6 passed), and `tests/test_canonical_cli.py -k 'layered_spa_public_manifest_preflights_runs_and_verifies_through_local_executor or public_noncluster_spa_schedules_round_trip_and_reconstruct'` (5 passed). The new tests make a two-check, nonconverging p=1/2 fixture and assert exact local-unit counts for execution and independent replay, selected C2V call sets/accounting, and randomized boundary refresh counts.
- files_changed: `src/bp_registry/canonical/schedules.py`, `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`, `tests/canonical/test_schedule_semantics.py`.
