# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern
hypotheses at the start of new investigations.

---

## phase5-source-semantic-gaps — BP intervention state and acceptance semantics
- **Date:** 2026-10-02
- **Error patterns:** previous-fresh damping history, missing first BP-SF flip, unconditional Restart root acceptance
- **Root cause(s):** V2C committed the raw proposal; BP-SF lacked the source zero baseline; Restart used syndrome validity without its weight gate.
- **Fix:** Commit the damped output, count from zero, and use an explicit conservative Restart weight certificate while recording the unavailable defect shortcut.
- **Files changed:** `memory.py`, `interventions.py`, `restarting.py`, focused tests, and source-decision documentation
- **Why not caught:** Existing tests encoded the damping error and lacked first-nonzero and overweight-valid-root fixtures; same-code replay was not an independent source oracle.
- **Recurrence guard:** Source-linked tests in `test_phase5_damping.py`, `test_perturbative_interventions.py`, and `test_restart_execution.py`, plus public replay tests.

---
