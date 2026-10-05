# Prelaunch methodology and implementation check (2026-10-05)

- The v2 design declares two rates, disjoint selection/evaluation namespaces, 128 selection shots per rate, 512/1280 evaluation shots, 5/10/20 extra iterations per unit, and both damping arms before sampling.
- Within each profile, the two methods receive the same in-memory initial BP result. Across profiles and damping levels, each rate/cohort uses the same physical shot IDs and observations. Selection and evaluation namespaces and seeds differ.
- Equal additional C2V caps are enforced at 8,640 updates. Actual initial/extra C2V work, branch/leg evidence, outcomes, and observed serial runtime remain separately recorded. A branch count is not treated as a compute-equivalent leg count.
- `selection-lock.json` is required before any evaluation shard; report recomputes its rule from hash-locked selection ledgers. The full evaluation parameter grid is retained, while four selected paired contrasts receive Holm correction.
- Source and environment hashes are frozen in `seal.json`; every shard has a frozen manifest, ordered shot ledger, deterministic replay check, and fixed-denominator result. The full report verifies all evaluation shards before writing claims.
- A tiny end-to-end two-rate, three-profile, two-cohort workflow passed. Fifteen focused tests passed, including parallel shot execution and a tampered-selection-lock rejection. Shell syntax and whitespace checks passed.
- Publication packaging is gated on the terminal report and verifies all 12 shard manifests, results, and losslessly compressed ledgers against the frozen selection lock and evaluation report. A checkout verifier checks every published file hash; a tampered compressed-ledger test passed.
- The dependent publication job commits only the manifest-listed evidence, checks the expected main ref before merging, re-verifies the merged checkout, runs the focused end-to-end test, and pushes main only after those gates pass.

The campaign remains a controlled BB72 CSS adaptation. It cannot validate either paper's circuit-level curves and does not complete Phase 6.
