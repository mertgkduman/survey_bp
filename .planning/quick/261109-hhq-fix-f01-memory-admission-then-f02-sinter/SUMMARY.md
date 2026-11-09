---
status: complete
workflow: gsd-quick --validate
baseline: 82311bd
implementation: 78f1c1c
---
# F01 then F02 completed

- `fd5c3d0`: reject preceding prior/field transforms before fixed-prior PD-prime consistently in local execution and compatibility admission. Retain supported fixed-prior memory and changing-prior/PDBP chains.
- `78f1c1c`: introduce observation-v2 identity and shared-v2 circuit ledgers; preserve exact shared-v1 replay and explicit legacy execution. Update capability inventory, migration documentation and regression fixtures.
- Qualification: 1,712 canonical/circuit tests passed, 20 skipped; final shared tests 161 passed; local/composition checks 38 passed. Suites overlap. The 20 skips are retained backend/optional checks; there was no fresh hardware run.
- Real Sinter worker: 24 v2 shots, complete binary execution unchanged when replayed one at a time. Historical shared-v1: 15 ledgers / 58 shots replay exactly. Legacy controls: 82 receipts byte-identical to baseline 872f7e1.
- Prior independent mathematics, native comparisons and 4,096 H200 shots remain source/evidence-bound. Only the four planned production files changed relative to the audited source set; numerical, Pauli and GPU implementations are unchanged.
- Result impact: 3,839 tracked data/experiment files scanned, hashed and unchanged from baseline. No affected tracked campaign found; no campaign rerun indicated by F01/F02. Untracked/private experiments are outside this exhaustive inventory.

Retained artifacts: [qualification.json](qualification.json), [result-impact.json](result-impact.json), [shared-v1-replay.json](shared-v1-replay.json), [capabilities.json](capabilities.json), test logs, Sinter ledgers and reproducible `qualify.py` / `sinter_smoke.py`.

The first qualification harness attempt reconstructed a serialized strict flooding-policy dataclass in Python mode; switching to JSON-mode validation fixed the harness. Its failure log remains in `qualification-harness-initial.log`. Only trailing whitespace was normalized in failing test logs; original hashes are in `log-normalization.json`.

HTML can proceed over the documented supported combinations and result statuses. Repeated identical observations share deterministic randomness in observation-v2; new randomized experiments must not append to a v1 Sinter resume identity. Existing Phase 11/Phase 5 scientific and review gates, Phase 7 pause, source-defined-counterpart scope and GPU exclusions remain unchanged.

See the [closure report](../../spikes/CANONICAL-KERNEL-SHARED-POLICY-FIXES.md) and [verification](VERIFICATION.md).
