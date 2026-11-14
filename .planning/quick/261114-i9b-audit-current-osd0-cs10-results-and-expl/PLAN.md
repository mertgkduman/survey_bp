---
id: 261114-i9b
type: quick
status: in_progress
---

# Check OSD results and explain the performance change

1. Inspect scheduler, frozen-source checks, terminal summaries and current worker progress. Recollect through the existing full-ledger/endpoint audit and regenerate the comparison report/catalog; preserve all raw samples and plans.
2. Explain the source-derived optimization from actual native and local code: affine solution reuse, packed GF2 XOR/popcount, uniform-channel scoring, and compiled traversal. Distinguish CS10-versus-CS10 standalone timings from paper CS60 and full BP decoding. Retain measured timing scope, tie handling and qualification limits.
3. Check same-rate LERs/intervals against previous BP-family results and paper CS60. Record running points separately from audited measurements, verify prior catalog evidence is unchanged and active-view counts reconcile, update STATE, commit and push.

No new simulations, altered frozen settings, canonical-kernel changes, phase-gate changes or native implementation edits.

Execution adjustment:212 completed points contain318M event rows, making a sequential interior-ledger refresh an hours-long operation. The exact existing refresh was moved to one-CPU Slurm61820674, with final complete collector61820676 serialized behind it and the original simulation array. This task performs a separate, explicitly labeled summary/manifest/CI/work and424-endpoint check for the immediate answer; it does not promote the212-point snapshot to fully audited publication evidence. A fresh -march=native reference benchmark checks compiler-target fairness without changing frozen receipts.
