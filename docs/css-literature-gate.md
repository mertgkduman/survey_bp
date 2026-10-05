# Small CSS literature-policy gate

This gate checks that three paper-linked decoder files use the **same researcher command** on matched B1 physical samples. It is a bounded mechanism and provenance check, not a reproduction of any published curve or a decoder ranking.

## Run or reuse a policy

Install the checkout with `python -m pip install -e .`, then use one command shape with the same study file:

```bash
OMP_NUM_THREADS=1 bp-registry data/studies/css-literature-b1-gate-v1.json \
  --decoder literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.toml \
  --results-root data/results/css-literature-gate-v1/cache

OMP_NUM_THREADS=1 bp-registry data/studies/css-literature-b1-gate-v1.json \
  --decoder literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.toml \
  --results-root data/results/css-literature-gate-v1/cache

OMP_NUM_THREADS=1 bp-registry data/studies/css-literature-b1-gate-v1.json \
  --decoder literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml \
  --results-root data/results/css-literature-gate-v1/cache
```

Each call returns JSON with `status: computed` when it creates evidence and `status: reused` when it has verified the existing ledger, result, and receipts. The importable equivalent is `bp_registry.study.ensure_study(study, decoder, results_root=...)`. The decoder-neutral study envelope compiles to the existing strict intervention or ensemble manifest schema; it retains the same artifact, p=0.000001, two shot IDs, seed, physical sample identity, denominator rule, and public work limits. This near-zero-noise smoke test exercises the command and provenance path; its two shots cannot estimate performance or test nontrivial B1 error correction.

The packaged manifest uses a repository-relative artifact root, and each result names its manifest and ledger relative to its cache directory. A clone with the same source files and pinned Python/NumPy/SciPy environment can use the three commands above to verify and reuse the Git results from a different checkout path. If a matching complete cache is absent, the same command computes it.

The [qualification inventory](../literature_policies/qualification-v1.json) accounts for all 14 requested source variants: ten [Yao BPGD](https://arxiv.org/pdf/2312.10950v2) records, three [Bhatnagar impulse](https://arxiv.org/pdf/2606.18240v1) records, and one [Rabeti–Mahdavifar MBBP-LD](https://arxiv.org/pdf/2605.14170v1) record. Every `.spec.toml` is a non-runnable source transcription. The paper-root `.toml` files are executable canonical adaptations whose registered controls are checked against those source records. Equations, paper anchors, and prose in a TOML file are provenance; only the policy tables compile into a decoder. Unknown policy kinds and unsupported combinations fail before sampling.

The selected Yao policy fixes **T=100, R=2** with flooding binary SPA and declared finite fixation. The selected Bhatnagar policy uses the source's **First_Convergence/0** variant, with a qualified flooding and finite-prior interpretation. The selected Rabeti policy uses normalized min-sum factor 0.875, serial checks, and the source frequency/(weight+1) list score, but only **two declared duplicate-row members**. Its maximal-subtree partition from the paper is unresolved. A no-member-converged return of zero is recorded as failure evidence, never admitted as a selected correction.

## Gate evidence and checks

The retained [evidence index](../data/results/css-literature-gate-v1/evidence-index.json) points to each compiled manifest, terminal ledger, result, computation receipt, and request receipt. The [replay summary](../data/results/css-literature-gate-v1/verification-summary.json) records the verified hashes and terminal counts. The [CLI reuse receipt](../data/results/css-literature-gate-v1/cli-smoke.json) records that an installed `bp-registry` call reused each output without changing the output identity, ledger hash, result hash, or shot denominator. To reproduce the gate checks:

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_css_literature_gate.py prepare --study data/studies/css-literature-b1-gate-v1.json
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_css_literature_gate.py run --study data/studies/css-literature-b1-gate-v1.json
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_css_literature_gate.py cli-smoke --study data/studies/css-literature-b1-gate-v1.json --bp-registry .venv/bin/bp-registry
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_css_literature_gate.py verify --study data/studies/css-literature-b1-gate-v1.json
```

Public replay reconstructs the decoder-visible run and verifies member/branch lineage, unique work, selection, terminal count, and original-syndrome checks. Request receipts bind the numerical computation to the exact policy file bytes and source metadata. A changed policy, artifact, engine source, budget, or study produces a different computation key; a damaged cached ledger or receipt fails reuse.

The cache also retains an explicitly [labeled p=0.005 exploratory interruption](../data/results/css-literature-exploratory-p005/README.md). Those cache keys are outside the frozen gate index and are not included in the gate's two-shot denominator for each policy.

## Scientific scope and next campaigns

The project B1 `[[882,24,18 ≤ d ≤ 24]]` candidate has pinned raw and semantic hashes and independently checked CSS algebra. Its **ordered matrix and logical-observable identity relative to each decoder paper's experiment remains unverified**. The authors' implementation revisions, full noise grids, denominators, digitized points, and statistical tolerances also remain unresolved. Therefore every gate result is `pilot_adaptation` and `not_assessed`; none is source-faithful, a published-curve reproduction, or a fair performance comparison. The [paper reproduction notes](../literature_policies/README.md) retain the code, noise, circuit applicability, parameter, and source gaps for each paper.

Phases 8–9 will collect exact CSS paper artifacts and run prespecified statistical comparisons. The completed [fair BB72 BeamSearch/RelayBP study](../data/studies/fair-beam-relay-css-v2.json) is separate controlled evidence; this gate does not rerun it. The Phase 5 visual review remains **human-pending**. Later quaternary and circuit phases remain in the first journal milestone.
