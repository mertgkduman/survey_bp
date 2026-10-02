---
phase: quick
plan: 261002-in6
status: complete
completed: 2026-10-02
commit: 77bf533
---

# Phase 6 candidate-list selection foundation

Implemented an immutable, deterministic original-space candidate-list selector in `src/bp_registry/canonical/list_selection.py`. It retains all candidate IDs, origins, declared eligibility bases, scores, original-syndrome validity, and rejection reasons. Selection requires a declared score basis, direction, and tie rule; hidden simulation truth is outside the interface. The module is generic infrastructure and does not claim source-defined BeamSearch ranking or voting semantics.

Documented the contract in `docs/phase6-candidate-selection.md` and added six small-code tests. Verification: `PYTHONPATH=src /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q tests/canonical/test_list_selection.py` passed (6 tests); `git diff --cached --check` passed before commit.

The work is isolated on branch `phase6-beam-search` so Phase 5's sealed p=0.05 verification and publication can finish from the original checkout.
