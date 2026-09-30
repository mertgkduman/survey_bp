---
quick_id: 260930-0vq
status: complete
completed_at: 2026-09-30
---
# Stopped and right-sized Phase 4 experiment

The Plan 04-13 production process group 3156090 was terminated. The shared Slurm allocation was left running. The GSD async manifest is terminal (`cancelled`), records the user's reason and retained receipt hash, and its resume command exits without launching work.

The retained B1 baseline receipt has 159 completed attempts and one interrupted attempt. No complete fresh evaluation, native-pair or factorial result existed at cancellation. All prior calibration and independent pilot evidence is preserved. The user judged the comprehensive experiment size premature; Phase 4 will now close through bounded evidence review, deterministic policy/source checks, an availability-aware notebook, and honest missingness. Any later CSS campaign in Phases 8–9 needs a new question, precision target, stopping rule and measured compute budget. Relay circuit reproduction remains in Phase 13.

Closed revised Plan 04-13 with a hash-linked retained evidence inventory and 30 passing Phase 4 evidence tests (one skipped). Updated the Phase 4 context, Plan 04-14, roadmap, public guide, state and handoff. No new simulation shots were launched. Validation: GSD async manifest schema passed; JSON parsed; `git diff --check` passed; observed production PIDs were absent.
