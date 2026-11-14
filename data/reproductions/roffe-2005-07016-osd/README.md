# Roffe canonical BP + OSD-0 / CS-10

Separate prospective campaign using the unchanged canonical BP kernel and the uniformly weighted, source-derived OSD processor qualified in Spike056. It preserves the historical failed Phase7 standalone-worker receipt and all earlier results. Native BP never runs in this campaign.

Four original toric codes [[162,2,9]], [[242,2,11]], [[338,2,13]], [[450,2,15]], with each code's original25/28-point Figure3 grid. Both new arms use X-only noise, original undamped canonical flooding min-sum, alpha_t=1-2^-t starting at1, float64, fixed matched prior and T=n. The processor is the only changed setting. OSD-0 and CS-10 use signed natural log(P0/P1) reliability ascending, original-column-ID ties, uniform-channel minimum Hamming weight, and first-enumerated minimum. These are explicit canonical adaptation conventions, not recovered author row/tie identity.

OSD runs only after BP fails its original syndrome at the iteration cap. Hidden simulation truth reaches only the later independent evaluator. Converged BP outputs bypass OSD, including those later identified as logical failures. The processor returns all original-coordinate candidates and weights; ledgers bind the full set digest and deterministic replay, original BP candidate and terminal posterior. Every selected candidate is checked against original H_Z before evaluation.

There are218 planned points:109 source strata times OSD-0/CS-10. Each stops at20 logical block failures or100,000,000 iid shots. Seed2026111413 shares the prior independent confirmation physical stream, enabling prefix checks; the decoder qualification seed is different and neither training nor prior results are pooled. A valid zero-failure upper bound remains a measured result. No phase-wide reproduction/superiority claim is assumed.

BP sweeps/edge updates and OSD cost remain distinct. Retain OSD invocation count, candidate evaluations, pivot probes, row-XOR words, triangular-solve words, affine direction/search operations, original checks and separate warmed BP/OSD times. Sorting item counts are explicit rather than fabricated comparison counts; these operands are not a universal scalar CPU-work unit. Stage timing includes the complete processor API including checks/provenance. Deterministic zero-syndrome warmup is excluded from sampled counts/work/time.

Candidate evaluations include the base OSD0 solution; the paper's k'+binomial(lambda,2) search count excludes that common base candidate.

## Run and inspect

```sh
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-osd/run.py --freeze
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-osd/run.py --test-only
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-osd/run.py --submit
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-osd/run.py --collect
```

One CPU/2GiB per point, array concurrency218, native threads1. Locked dispatch receipts prevent duplicate jobs. A successful full array triggers complete-ledger/manifest/work/endpoint audit, table/report generation and catalog refresh. Partial manual collection preserves missing values and the shared multi-rate eligibility rule. Raw chunks contain at most4096 retained shots to reduce filesystem metadata overhead; exact contiguous resume and stopping prefixes are audited. Worker failures prevent dependent publication. Existing MacKay jobs are not touched.

Public source reference: https://github.com/quantumgizmos/ldpc/tree/d3429964cd4ffe1abfc041c6ec8b8425cb174f40 (MIT). Qualification and native/oracle/benchmark evidence: .planning/spikes/056-efficient-osd/. This processor is qualified for a uniform binary channel; no unsupported general Pauli/nonuniform OSD API is claimed. The paper's CS60 source comparison remains separate context.
