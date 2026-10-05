---
status: complete
quick_id: 261005-kcm
date: 2026-10-05
---

# Literature policy registry scaffold

Created `literature_policies/` with a per-paper template and separate locations for executable decoder TOML files and mapped-only source specifications. The registry contract requires primary-source anchors, exact revision, algorithm equations and control flow, code/circuit/noise/result inventory, adaptation status, unresolved details, and distinct reproduction assessment. It aligns policy extraction with the roadmap while deferring actual code/circuit artifacts and statistical reproduction to their dedicated phases.

Implementation commit: `660bdd8`. No paper-specific folder or decoder claim was created before the user supplies the selected papers and variants. No simulation code changed.
