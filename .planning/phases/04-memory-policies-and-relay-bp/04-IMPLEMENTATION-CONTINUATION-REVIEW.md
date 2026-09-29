---
phase: 04-memory-policies-and-relay-bp
workflow: gsd-execute-phase
scope: committed implementation continuation only
date: 2026-09-27
status: bounded_findings_resolved
rechecked_commits: [9a8e11c, 7429408, ebd9c01, 0185d1e]
---

# Bounded continuation review

This records the read-only review of the isolated implementation continuation.
It is not a Phase 4 scientific, goal, security or completion verdict. The
reviewer inspected committed source and tests; the live calibration checkout,
partial outcomes and uncommitted source were excluded.

The native observation binding finding is resolved in `9a8e11c`: the reader
reconstructs the exact public observation and gamma draws, repeats the pinned
author adapter translation, and compares the retained native payload rather
than accepting a self-consistent transcript alone.

The four local execution/trace findings are resolved in `7429408`:

1. Local replay uses the declared min-sum/NMS/OMS kernel and parameter
   assignment, matching execution rather than hardcoding SPA.
2. A numerical-failure memory sidecar is compared with independently rebuilt
   committed history, beliefs and candidate prefix; rehashed alteration fails.
3. A non-memory V3 local numerical failure after admitted work reconstructs
   its truthful committed prefix from qualified work/schedule evidence.
4. Optional sidecar finalization failures emit a typed unavailable trace link
   and preserve decoder work/terminal evidence.

Earlier local field clipping/history discrepancies and missing semantic trace
proof were corrected in `0c5789f`; its legacy-identity repair omits absent
assignments and trace-off controls, retaining frozen V2/V3/Relay identities.
The earlier run-ID transplant concern was retracted because the compact
manifest already binds run identity.

The campaign reader retains full terminal/outcome/population/work validation
when reusing its request-scoped ledger and context caches. The reviewer found
no qualification shortcut in the caching delta. A hash-before/path-read split
could, however, cache parsed bytes under another byte digest; before/after
hashes reject ordinary replacement but not restoration during a read. The
final correction consumes one byte buffer for parsing and digest identity,
and separately reuses static manifest validation while deriving every shot
observation with the existing sampling arguments.

The exact-buffer correction is `ebd9c01`, using the pure APIs from `30132a2`.
The reviewer also found that a shallow-frozen shared manifest context exposed
mutable code and controls across shots. `0185d1e` stores private static facts and
returns deep-detached public views and shot contexts without repeating algebra.
Its mutation-isolation test changes returned matrices, policy parameters and
work controls before comparing the next shot with an independent public wrapper.

The final bounded recheck found no residual concrete defect in the corrected
native observation, local replay/trace, helper/cache byte identity or sampling
preservation scope. No full-phase review or completed-plan count is inferred
from these resolutions.

The full continuation regression then exposed an unconditional optional prior
keyword reaching the legacy Hsu executor/replayer, plus four old admission
expectations. `62fe977` restricts the keyword to actual memory execution and
tests the implemented/rejected matrix through public round trips. Targeted
gates passed 7 Hsu, 9 admission/min-sum and 4 local/numerical checks. The final
full suite passed **532 tests, with one existing skip**, in **547.39 seconds**.
The skip is unchanged; these results remain implementation validation rather
than a scientific phase verdict.
