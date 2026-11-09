---
status: complete
baseline: 82311bd
workflow: gsd-quick --validate
execution: inline; no subagents requested
---
# Fix shared-policy findings F01 then F02

User authorization: implement both reviewed fixes, then proceed to HTML with qualified results. Preserve source-defined counterparts, prior evidence, GPU subset and scientific publication gates.

## Task 1 — F01 admission (first)
Files: canonical/memory_execution.py; local-memory and shared-policy regression tests.
Reject PD-prime after a preceding prior transform on every local schedule, using the existing fixed-prior rule. Retain isolated PD-prime and compatible ordered memory. Correct the prior failure-injection test to use a supported changing-prior/field chain. Retain failing evidence, then run local-memory/shared/circuit regressions; commit the fix independently.

## Task 2 — F02 versioned circuit identity (second)
Files: circuit/shared_policies.py; shared decoder tests; circuit regression tests; capability inventory and usage/contracts docs.
Make new shared Sinter execution use observation-v2: hash a versioned model/policy context and normalized detector bytes. No batch index, append order, mutable counter or worker ID enters the key. Repeated identical observations deliberately share a deterministic random stream under one policy/seed. CPU callers retain explicit trial IDs. Emit circuit-shared-policy-ledger-v2; support exact old v1 replay using batch-index-v1 selected from the stored schema. Unknown identity/schema or mismatched metadata rejects. Preserve existing v1 bytes and test factory/direct construction, batch splitting/reordering, separate instances/pickling, packed padding, identity-dependent policy families and old receipts. Commit separately.

## Task 3 — qualification and clean-result record
Files: task qualification scripts/receipts, docs, STATE.md and spike manifest closure link.
Run targeted regressions, real Sinter worker smoke with randomized v2, old shared-v1 ledger replay and 82 baseline legacy receipts. Carry unchanged Pauli/GPU math by hashes. Recheck tracked result manifests for affected use; preserve all existing campaign files and identify any necessary selective rerun. Produce source-hashed qualification, closure report and updated support inventory for HTML. No campaign ranking, new GPU run, release packaging or publication promotion.

## Acceptance
- F01 counterexample fails at admission before execution; fixed-prior PD-prime still runs and replays.
- F02 reproducer has identical per-observation predictions, candidate/work/lineage across chunking/permutation/instances; old shared-v1 receipts still replay byte-for-byte.
- Full policy/input/result admission remains closed; v2 identity changes are explicit in evidence and Sinter configuration guidance.
- Appropriate regression suite and retained scientific/legacy controls pass against final source.
- Both findings closed with evidence; HTML can consume the qualified subset; no unsupported clean-results claim.

## Inline plan check
Passed: two known bounded findings, separate commits in requested order, existing files observed live, explicit v1 compatibility and v2 semantics, no extra policy invention. No clarification or external approval is needed.
