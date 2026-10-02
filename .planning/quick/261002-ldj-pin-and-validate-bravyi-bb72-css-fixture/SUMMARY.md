---
status: complete
quick_id: 261002-ldj
date: 2026-10-02
---

# BB72 fixture frozen

Pinned the Bravyi author repository at `fa77e3333d3ec44c79d8f914dd24c040d1da471b` and required its unique commented `[[72,12,6]]` parameter block. The freeze tool reconstructs Hx and Hz without executing the author's circuit script, then derives a deterministic project logical basis. The immutable artifact and provenance include whole-artifact and per-matrix hashes.

Independent construction checks establish `Hx,Hz=(36,72)`, GF(2) ranks `30,30`, `k=12`, CSS commutation, row/column weights and paired logical operators. Three focused tests passed. Distance 6 is source reported, not independently certified. This is an input fixture and one-shot smoke manifest, not a performance comparison or reproduction assessment.

The public V3 manifest passed strict preflight with the declared CPU environment. Its one-shot canonical run produced a ledger that passed deterministic replay verification; the one-iteration shot ended at its cap without a candidate, as expected for a smoke check.

Files: `tools/freeze_bb72_source.py`, `data/artifacts/bb72-css.json`, `data/artifacts/bb72-css.provenance.json`, `data/manifests/phase3-pilot-bb72.json`, `tests/test_bb72_fixture.py`.
