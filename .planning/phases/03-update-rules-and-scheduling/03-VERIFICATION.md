---
phase: 03-update-rules-and-scheduling
verified: 2026-09-24T15:35:13Z
status: passed
score: 5/5 must-haves verified
requirements_verified: [UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05, SCH-06]
behavior_unverified: 0
human_verification: []
gaps: []
---

# Phase 3: Update Rules and Scheduling Verification

**Goal:** A researcher can vary requested message-update and scheduling policies without changing the canonical engine or losing semantic and cost visibility.

**Verdict:** Passed. All 17 plans have summaries; the GSD phase-completeness query reports no incomplete plans, orphan summaries, errors, or warnings. The full current suite passes with 300 tests. Public `verify-run` reconstructs the retained Phase 3 policy comparison and the new Hsu group pilot.

## Goal-Backward Checks

| Roadmap success criterion | Evidence | Verdict |
| --- | --- | --- |
| 1. Named min-sum variants with explicit equations and small-graph calculations | `src/bp_registry/canonical/updates.py`; `tests/canonical/test_update_rules.py` checks signed minimum, normalized assignments, and offset boundaries; V3 public manifests execute and verify. | Passed |
| 2. Layered and serial update units, order, and message visibility | `src/bp_registry/canonical/schedules.py`; `tests/canonical/test_schedule_semantics.py` checks layer snapshot/commit, check-node serial, variable-node serial, partition rejection, and rollback. | Passed |
| 3. Residual work and randomized replay separated from physical sampling | `src/bp_registry/canonical/residual.py`, `schedules.py`, and `budgets.py`; residual and randomized tests cover priority invalidation, setup work, replay, and denied-order state preservation. | Passed |
| 4. Source-defined cluster sequence with explicit construction and parameters | [Hsu et al., arXiv:1202.1060v1](https://arxiv.org/html/1202.1060) is pinned in `03-SOURCE-REVISION.md`; `group_shuffled.py` executes the paper's worked size-two, overlap-one groups and records order, overlap, source ID, root/derived RNG identities, and work. There is no learned parameter in this Hsu configuration. Manifest preflight rejects a Moradi source claim or incompatible controls. Two retained BB-144 CSS shots independently verify. | Passed |
| 5. Matched policy pilots with raw costs and defined compatibility | `data/results/phase3-pilots` retains 19 verified one-shot policy terminals across matched code/sample cohorts and a strict unsupported-combination rejection; `reports/phase3-pilots` and the executable notebook retain work categories, missing outcomes, and scoped runtime. The separate Hsu pilot adds two source-qualified terminals. | Passed |

## Requirement Traceability

| Requirement | Current evidence |
| --- | --- |
| UPD-01, UPD-02, UPD-03 | Explicit min-sum, NMS, and OMS contracts, equations, small-graph tests, and V3 public pilot manifests. |
| SCH-02, SCH-03 | Layered, check-node serial, and variable-node serial implementations; message-order, budget, and public replay tests. |
| SCH-04 | Huang–Ueng conventional sRBP source pinning, residual cache/priority semantics, and budget tests. |
| SCH-05 | Declared randomized layered order, replay identities, and physical-sample separation tests. |
| SCH-06 | Hsu source revision, group constructor and local-step tests, strict public manifest, retained ledger/result, and rehashed semantic-tamper rejection. |

All eight IDs declared in the Roadmap appear in Phase 3 plan frontmatter and have executable evidence. GSD artifact and key-link queries succeeded on all 17 plans.

## Public Evidence and Reproduction Boundary

The retained [Hsu manifest](../../../data/manifests/phase3-hsu-group-pilot.json) and [result](../../../data/results/phase3-hsu-group-pilot/result.json) use `pilot_adaptation` / `not_assessed`. The two terminal shots are one completed exact recovery after 70 group units and one 72-unit limit. Both remain in the denominator. The [ledger](../../../data/results/phase3-hsu-group-pilot/events.jsonl) records the realized group order, work and progress, and separate setup/decode time. Public `verify-run` passes, and rehashed edits to source, order, work, or cursor fail.

The Hsu work is a binary CSS syndrome adaptation of a classical AWGN LDPC schedule, with a declared post-group stopping adaptation. It is not a reproduction of the paper's classical curves. Moradi RL-S remains unavailable without its author Q-table and ordered partition, and its separate qualifier does not execute a substitute. The user-supplied [arXiv:2504.01728](https://arxiv.org/pdf/2504.01728) is recorded for later bit-flipping and diversity-policy research; it does not define this group schedule.

## Gates

- `node /hpc/home/mg551/.codex/gsd-core/bin/gsd-tools.cjs verify phase-completeness 03` — 17/17 complete, no errors or warnings.
- GSD `verify artifacts` and `verify key-links` — all 17 plans returned success.
- `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 300 passed.
- `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/phase3-hsu-group-pilot` — 2 verified terminal rows.

No human-only goal check is needed. Statistical agreement with any published curve remains `not_assessed` and is outside this phase's source-procedure execution claim.
