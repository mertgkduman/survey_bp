---
status: complete
quick_id: 261002-mjc
date: 2026-10-02
---

# Parallel v2 verification prepared

The v2 finalizer now replays all 14 arm ledgers concurrently using the public `verify_run` operation, then performs the same design/ledger hashes, arm manifest/result, aggregate byte, and matched physical-sample checks as the sealed v2 verifier. The v2 run script and its pinned design were not changed.

The aggregate checker passed against the retained v1 ledger as a structural test (the v1 run remains scientifically invalid), and rejected a deliberately corrupted ledger digest. Python compilation and `git diff --check` passed. The previous one-core finalization/publication dependencies were cancelled and replaced with 14-core finalization and gated publication jobs.
