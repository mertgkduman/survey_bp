# Shared-policy corrections qualified for HTML integration

Both confirmed findings from [audit 050–053](CANONICAL-KERNEL-SHARED-POLICY-AUDIT.md)
are closed, in the requested order, against implementation `78f1c1c`.
The supported interface can now be used by HTML with its recorded capability,
identity and scientific-evidence boundaries. This is engineering qualification;
it does not promote unfinished publication studies.

## Corrections

| Finding | Correction | Compatibility |
|---|---|---|
| F01: a changing affine prior could precede fixed-prior PD-prime on local schedules; its effect was discarded | `fd5c3d0` rejects every preceding transform before PD-prime in local execution and the declarative compatibility resolver | Fixed-prior PD-prime and supported downstream transforms remain available; affine prior plus PDBP remains supported. Historical invalid combinations require their pinned source and cannot be described as effective combined decoders. |
| F02: shared Sinter randomized execution used a batch-local row index | `78f1c1c` introduces observation-v2: hash the versioned model/full-policy context and normalized detector bytes | New shared-v2 execution is independent of batching, ordering, instances and workers. Shared-v1 ledgers replay exactly with their original batch-index identity; explicit legacy execution is retained. |

Repeated identical observations deliberately use the same random stream under
the same model and policy seeds. Independent randomized replicas require distinct
policy seeds; CPU users can supply explicit shot identities. Sinter does not
supply global shot IDs. The full semantics and migration rules are in the
[support guide](../../docs/shared-policy-support.md#random-identity-and-historical-replay).
Use a new Sinter decoder name and resume identity when moving from v1 to v2.

The new identity caches its model/policy digest at compilation and hashes only
the digest plus normalized detector row per shot. Numerical loops, compiled
dispatch and the qualified GPU subset are unchanged. No new throughput claim
is made by this correction.

## Verification

The [qualification receipt](../quick/261109-hhq-fix-f01-memory-admission-then-f02-sinter/qualification.json)
binds current source and retained evidence hashes. Tests overlap and their counts
must not be added together.

| Evidence | Result |
|---|---|
| Canonical and circuit regression on final production source | 1,712 passed, 20 skipped |
| Final shared decoder tests, including schema downgrade rejection | 161 passed |
| Final local-memory/composition admission checks | 38 passed |
| Random-identity consumers across batch splitting, permutation, repeat observations, pickling and concurrent calls | 25 policy configurations preserve complete per-shot execution |
| Actual Sinter worker with randomized serial, grouped and disordered-memory policies | 24 shots; exact per-shot rebatching and ledger verification |
| Legacy CPU/controller and circuit controls | 82 receipts byte-identical to baseline 872f7e1 |
| Earlier shared-v1 ledgers, including the original chunking counterexamples | 15 ledgers / 58 shots replay exactly |
| Independent mathematics and aligned upstream comparisons | Prior 2,880 and 1,188 cases carried after source checks |
| Pauli/GPU implementation and prior hardware evidence | Unchanged; prior 4,096 H200 shots retained by hashes; no new GPU run |

The initial F01/F02 failing tests are retained. A qualification-harness attempt
used Python-mode validation on a serialized strict dataclass; the harness was
corrected to use JSON-mode policy reconstruction and rerun successfully. This
was a harness construction error, with its initial log preserved.

## Existing results and the HTML boundary

The [result-impact inventory](../quick/261109-hhq-fix-f01-memory-admission-then-f02-sinter/result-impact.json)
scanned and hashed 3,839 tracked files under the declared data/experiment roots.
They are unchanged from task baseline `82311bd`. No tracked campaign uses the
shared Sinter schema or the invalid affine-prior/PD-prime composition; the three
PD-prime mentions match the earlier audit's unchanged evidence/schema files.
**No campaign rerun is indicated by these two fixes for that inventory.**

Historical shared-v1 engineering receipts retain their original semantics.
New randomized Sinter runs can produce different outcomes under observation-v2
and must use a new experiment identity. An external or untracked campaign using
an affected configuration needs its own assessment; this scan does not certify
all private artifacts or remove existing scientific limitations.

HTML should consume [policy-capabilities-v2](../quick/261109-hhq-fix-f01-memory-admission-then-f02-sinter/capabilities.json)
and the existing result manifests, showing kernel/identity version, backend,
source/adaptation status and result qualification. Phase 11 scientific gaps,
Phase 5 human review and the paused Phase 7 work remain as recorded. Historical
audit verdicts and campaign files have not been rewritten.
