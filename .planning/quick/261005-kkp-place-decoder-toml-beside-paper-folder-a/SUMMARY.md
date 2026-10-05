---
status: complete
quick_id: 261005-kkp
date: 2026-10-05
---

# Paper folder layout

Decoder TOML files now live directly in `literature_policies/<paper-id>/`. Paper-specific source and reproduction details live in `literature_policies/<paper-id>/paper_reproduction/`. The template inventories code, circuits, noise, published results, source revisions, equations, and missing details. Mapped-only specifications are labeled `.spec.toml` and remain non-executable until their policies have been validated and implemented.

The original storage checkout and the integration Git worktree are separate working directories for the same repository. The original checkout is aligned with published main after this change; its local untracked simulation evidence is preserved.

Implementation commit: `1ad21ba`. No simulation code changed.
