---
id: 261117-h97
status: complete
campaign_status: unchanged
---

# Released PriorTilt scoring uses observable agreement, not joint recovery

Current public Rust/Python/adapter/simulation helper blobs match the campaign's pinned8eefd37d694b5942fe60ec6d5c82ce97f3d2a450 source. Internal BP syndrome comparison is present and drives first-valid stopping. If the budget is exhausted, the final possibly invalid hard decision is returned with convergencefalse. Both Python decode paths always project it through A. The Sinter adapter supplies predicted observable bits only, without per-shot convergence gating, forced failure or discard. Sinter's observed-XOR-predicted counter and the author's direct timing helper therefore score observable mismatch unconditionally. The simulation's errors/shots/cycles calculation adds no syndrome criterion.

A source-native executable proof with a reachable synthetic syndrome and no duplicate detector supports passes: truee=[1,1,0,0] gives s=[1,1,0] and observable1; two valid-config zero-offset sweeps return ehat=[1,1,1,1], estimated syndrome[0,0,0], convergencefalse, and observable1. The actual single and packed Sinter wrappers pass that correct observable prediction. This proves the semantic difference; it is not a paper-budget performance run. The binary matches the earlier frozen source qualification. No source code was patched.

The strict joint failure is observable failure plus the disjoint case of nonconvergence with correct observables. Our existing canonical BB144/.002 Z-memory ledger contains one such case in1,192,846 shots:20 observable errors versus21 failures under both-equations recovery on that same prefix. Its per-shot records permit a separate stricter stopping prefix to be reconstructed without resimulation. This is our canonical data, not the author's historical frequency. Public author CSVs do not supply the joint convergence/observable contingency counts, so strict recovery rates for their historical runs cannot be recovered from those totals alone.

Our reproduction deliberately uses released observable-only scoring and records convergence/joint counts separately. No running job, metric, stopping target, frozen/source/kernel files or existing result was changed. Detailed primary-source line links and interpretive limits are in FINDINGS.md; executable proof and hashes are in probe.py/probe.json/verification.json. Other collectors' pre-existing modified files remain unstaged. Phase gates/counters and model/public/v1 state are unchanged.
