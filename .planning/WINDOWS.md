---
schema_version: 1
open_count: 11
waived_count: 0
fixed_count: 3
total_count: 14
last_updated: 2026-10-07T19:54:56.747Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | deviation | src/bp_registry/canonical/schedules.py | 140 | Single-neighbor check indexing was corrected to preserve a one-element incoming message buffer. | fixed |  | 2026-09-23T08:23:47.117Z | 2026-09-23T08:23:59.510Z |
| 2 | 02 | deviation | src/bp_registry/canonical/profiling.py |  | Restrict retained thread environment values to validated positive counts. | fixed |  | 2026-09-23T09:15:05.961Z | 2026-09-23T09:15:31.774Z |
| 3 | 03 | deviation | tests/canonical/test_schedule_semantics.py |  | Fixed new layered replay test helper before Task 1 completion | fixed |  | 2026-09-24T09:43:35.988Z | 2026-09-24T09:43:53.726Z |
| 4 | 04 | skipped-test | tests/canonical/test_memory_policies.py | 31 | Source-qualified damping, PDBP, PD′BP, and momentum equation test is deferred to Wave 1. | open |  | 2026-09-24T23:03:27.075Z |  |
| 5 | 04 | skipped-test | tests/canonical/test_memory_composition.py | 30 | Seeded assignments, schedule compatibility, and budget-denial rollback fixture is deferred to Wave 1. | open |  | 2026-09-24T23:03:27.643Z |  |
| 6 | 04 | skipped-test | tests/canonical/test_relay_differential.py | 8 | Pinned author v0.2.2 Relay differential needs the reviewed external environment and observer patch. | open |  | 2026-09-24T23:03:28.243Z |  |
| 7 | 04 | skipped-test | tests/canonical/test_relay_differential.py | 13 | Observer patch equivalence needs the reviewed external author reference build. | open |  | 2026-09-24T23:03:28.838Z |  |
| 8 | 04 | skipped-test | tests/canonical/test_phase4_evidence.py | 19 | B1 digest reconciliation and bounded notebook reuse evidence are deferred to Wave 1. | open |  | 2026-09-24T23:03:29.449Z |  |
| 9 | 04 | unrun-verify | tests/test_canonical_cli.py | 21 | Inherited canonical CLI verification is blocked because .venv subprocesses cannot import bp_registry. | open |  | 2026-09-24T23:03:30.055Z |  |
| 10 | 04 | unrun-verify | scripts/qualify_relay_v022.py |  | Author decode_144_12_12 full native test exceeded the 720-second qualification bound and remains inconclusive. | open |  | 2026-09-25T02:50:48.185Z |  |
| 11 | 07 | unrun-verify | tests/canonical/test_postprocessing_handoff.py |  | Planned SI handoff regression was unavailable because the test file is absent from this checkout. | open |  | 2026-10-06T04:59:35.849Z |  |
| 12 | 10 | deviation | scripts/qualify_phase10_native_asced.py |  | Replaced unreliable exact-commit git ls-remote query with pinned GitHub commit API identity | open |  | 2026-10-07T03:20:07.789Z |  |
| 13 | 10 | deviation | src/bp_registry/quaternary/asced.py |  | Partial splitter search uses incremental rank/detectability before full even-Delta qualification. | open |  | 2026-10-07T19:54:56.115Z |  |
| 14 | 10 | deviation | src/bp_registry/quaternary/asced.py |  | aSCED affine graphs use a dedicated immutable working graph because qualified splitter rows are noncommuting. | open |  | 2026-10-07T19:54:56.747Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "02",
    "file": "src/bp_registry/canonical/schedules.py",
    "line": 140,
    "description": "Single-neighbor check indexing was corrected to preserve a one-element incoming message buffer.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-23T08:23:47.117Z",
    "resolved_at": "2026-09-23T08:23:59.510Z",
    "milestone": "v1.0"
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "02",
    "file": "src/bp_registry/canonical/profiling.py",
    "line": null,
    "description": "Restrict retained thread environment values to validated positive counts.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-23T09:15:05.961Z",
    "resolved_at": "2026-09-23T09:15:31.774Z",
    "milestone": "v1.0"
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "03",
    "file": "tests/canonical/test_schedule_semantics.py",
    "line": null,
    "description": "Fixed new layered replay test helper before Task 1 completion",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-24T09:43:35.988Z",
    "resolved_at": "2026-09-24T09:43:53.726Z",
    "milestone": "v1.0"
  },
  {
    "id": 4,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/canonical/test_memory_policies.py",
    "line": 31,
    "description": "Source-qualified damping, PDBP, PD′BP, and momentum equation test is deferred to Wave 1.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:27.075Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 5,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/canonical/test_memory_composition.py",
    "line": 30,
    "description": "Seeded assignments, schedule compatibility, and budget-denial rollback fixture is deferred to Wave 1.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:27.643Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 6,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/canonical/test_relay_differential.py",
    "line": 8,
    "description": "Pinned author v0.2.2 Relay differential needs the reviewed external environment and observer patch.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:28.243Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 7,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/canonical/test_relay_differential.py",
    "line": 13,
    "description": "Observer patch equivalence needs the reviewed external author reference build.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:28.838Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 8,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/canonical/test_phase4_evidence.py",
    "line": 19,
    "description": "B1 digest reconciliation and bounded notebook reuse evidence are deferred to Wave 1.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:29.449Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 9,
    "kind": "unrun-verify",
    "phase": "04",
    "file": "tests/test_canonical_cli.py",
    "line": 21,
    "description": "Inherited canonical CLI verification is blocked because .venv subprocesses cannot import bp_registry.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-24T23:03:30.055Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 10,
    "kind": "unrun-verify",
    "phase": "04",
    "file": "scripts/qualify_relay_v022.py",
    "line": null,
    "description": "Author decode_144_12_12 full native test exceeded the 720-second qualification bound and remains inconclusive.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-25T02:50:48.185Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 11,
    "kind": "unrun-verify",
    "phase": "07",
    "file": "tests/canonical/test_postprocessing_handoff.py",
    "line": null,
    "description": "Planned SI handoff regression was unavailable because the test file is absent from this checkout.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-06T04:59:35.849Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 12,
    "kind": "deviation",
    "phase": "10",
    "file": "scripts/qualify_phase10_native_asced.py",
    "line": null,
    "description": "Replaced unreliable exact-commit git ls-remote query with pinned GitHub commit API identity",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-07T03:20:07.789Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "10",
    "file": "src/bp_registry/quaternary/asced.py",
    "line": null,
    "description": "Partial splitter search uses incremental rank/detectability before full even-Delta qualification.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-07T19:54:56.115Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "10",
    "file": "src/bp_registry/quaternary/asced.py",
    "line": null,
    "description": "aSCED affine graphs use a dedicated immutable working graph because qualified splitter rows are noncommuting.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-07T19:54:56.747Z",
    "resolved_at": null,
    "milestone": "v1.0"
  }
]
````
