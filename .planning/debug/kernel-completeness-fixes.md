---
status: fixing
trigger: "fix in the recommended order"
created: 2026-11-08
updated: 2026-11-08
---

## Current Focus
hypothesis: The five audit findings arise at separate admission, ownership, context, posterior and export boundaries.
next_action: Fix D03 then D04 then D01 then D02 then D05, with isolated regressions and final integration/performance checks.

## Symptoms and evidence
Prefilled from CANONICAL-KERNEL-COMPLETENESS-AUDIT.md at 6f68961. Eight D01 context failures, two D02 posterior failures, five D03 constructor failures, three D04 ownership failures and one D05 false export. Full baseline suite 2109 passed, one skip, 25 fork warnings. No need to repeat symptom questions. Execute inline under the skill's no-automatic-spawn restriction.

## Resolution contract
Preserve historical spikes 008–037. Separate functional commits in the approved order. Retain failing/passing tests in new spikes 038–042. Keep numerical profile identities, public manifest defaults, phase position and publication gates unchanged. Explicitly name corrected iteration-context execution and retain historical replay support.

D03 committed 630a934: all circuit construction paths validated; 50 circuit checks passed. D04 ownership closure: 340 focused checks passed. Next: D01 context propagation and replay semantics.
