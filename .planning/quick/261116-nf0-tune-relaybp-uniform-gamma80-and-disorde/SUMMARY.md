---
id: 261116-nf0
status: complete
campaign_status: running
implementation_commit: 177417b7
simulation_array: 61942447
collector: 61942448
point_workers: 12
fresh_audited_workers: 0
phase_gates_changed: false
---

# RelayBP gamma tuning launched

The user confirmed one 80-iteration uniform-gamma leg followed by one 60-iteration disordered-gamma leg: **140 maximum sweeps per CSS component**. Syndrome convergence stops a leg early and skips the second leg if the first succeeds. Gamma controls prior memory and is distinct from V2C damping. The study uses Relay Eq. 4 from [arXiv:2506.01779v2](https://arxiv.org/html/2506.01779v2); this two-leg code-capacity adaptation does not reproduce that paper's circuit results or 301-leg budget.

The separately frozen study is `data/reproductions/lp1054-relay-gamma80-60`. It retains the exact LP1054 code, depolarizing rates .02/.04/.06/.08/.10/.12, both-component logical evaluator and qualified canonical BP/search primitives. Twelve workers cover six rates and two numerical backgrounds: source NMS (damping 0, alpha .625, offset 0) and the parent's training-selected BP settings. All six parent selection locks and referenced training summaries are pinned; parent fresh outcomes never enter selection.

Each worker tests 199 coarse policies: 11 uniform gamma values crossed with 18 disorder intervals, plus exact zero memory. Independent finalist and refinement cohorts retain gamma diversity and explore local neighbors. Selection minimizes refinement LER among genuine disorder policies, then mean sweeps and latency. Independent fresh confirmation compares the selected policy, each phase alone, reset-zero gamma, and continuous BP140. Exact duplicates share a cohort with multiple role labels. Every unique fresh policy stops at **20 logical failures or 100 million shots**. Noise and memory streams are separate; disordered per-variable gamma remains fixed during its 60-iteration leg.

All BP work, gamma-bias updates, disordered RNG draws, clips and per-leg provenance are retained. New latency includes both component solvers and controller/path storage, excluding external hashing, serialization, sampling and evaluation. It must not be directly ranked against earlier provenance-instrumented timing. Immutable 1024-shot chunks, atomic metadata and deadline requeue preserve exact resume.

Array **61942447** runs 12 point workers, each with one CPU and 3 GiB. Each simulation is followed by a separate audit process in the same allocation. Collector **61942448** waits for successful completion of the array; it requested one CPU/16 GiB, while Slurm reports two reserved collector CPUs. Earlier campaigns continue unchanged. All new workers began coarse tuning without logged errors; no fresh gamma results are published yet.

Validation passed: **64 scientific tests, 56 catalog tests, 11 Chromium workflow groups**, and 96 independent qualification shots across 12 policies. Scalar checks cover exact 80/60 traversal on toy and real LP1054 checks, messages/posteriors/lineage, early stopping, quenched gamma, exact fixed-coefficient controls, typed work, tampering, selection and restart. Frozen source/software/code/parent pins were checked after launch.

The empty dataset is registered centrally and admits only audited fresh evidence through the existing exact-policy multi-rate projection. Browser checks cover gamma labels/exports, specialized saved-decoder protection, same-rate disqualification, stale selections, custom inputs and v1. The active view remains **443 curves / 3194 points / 13 codes / 0 circuits**; all 1543 historical raw series preserve their point multiplicities. Earlier raw evidence, manifests, frozen sources, canonical kernels, v1, model settings and phase gates/counters are unchanged. Gamma benefit remains pending independent fresh evidence.
