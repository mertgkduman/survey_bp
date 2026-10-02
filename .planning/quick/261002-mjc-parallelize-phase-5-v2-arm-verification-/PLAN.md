---
status: in_progress
quick_id: 261002-mjc
date: 2026-10-02
---

# Parallelize Phase 5 v2 arm verification before publication

## Goal

Verify each of the 14 independent corrected B1 arm ledgers concurrently, then perform the same aggregate, digest, and paired-sample checks as the sealed v2 verifier. Preserve verification semantics and reduce wall time before GitHub publication.

## Tasks

1. Add a parallel verification path to the v2 finalizer without changing the sealed v2 run script or design digest.
2. Compare the aggregate checks with the existing verifier, test on retained v1-format evidence without treating that evidence as valid results, and run syntax/focused checks.
3. Replace the pending one-core finalization job with a 14-core dependent job and rebind the publish dependency.
4. Commit and push the changes so the publication job's HEAD guard remains valid.
