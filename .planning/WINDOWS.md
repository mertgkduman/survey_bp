---
schema_version: 1
open_count: 0
waived_count: 0
fixed_count: 3
total_count: 3
last_updated: 2026-09-24T09:43:53.726Z
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
  }
]
````
