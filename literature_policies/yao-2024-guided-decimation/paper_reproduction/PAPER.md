# Yao et al. — binary BP guided decimation

## Primary source and status

- Paper: Hanwen Yao, Waleed Abu Laban, Christian Häger, Alexandre Graell i Amat, and Henry D. Pfister, *Belief Propagation Decoding of Quantum LDPC Codes with Guided Decimation*, [arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2), 21 June 2024.
- Anchors: binary BP in Section 3; BPGD in Section 4.3 and Algorithm 1; Figure 3 varies `T`; Section 4.6 and Figure 6 vary `R`.
- Author implementation identity: unverified. Do not infer source-exact execution from the canonical implementation.
- All ten `.spec.toml` files are **non-runnable source records**. Separate paper-root `bp-t100.toml`, `bpgd-t001.toml`, and `bpgd-t100-r002.toml` files are runnable **canonical adaptations** through the public command. The other seven source variants have typed mappings but no paper-root runnable file yet. Exact source-experiment qualification remains open.

## Requested decoder variants

| File in parent folder | Source control | Target |
| --- | --- | --- |
| `bp-t100.spec.toml` | Plain binary BP, 100 iterations | Figures 3 and 6 comparator |
| `bpgd-t001.spec.toml` | BPGD, T=1, R defaults to code length | Figure 3 |
| `bpgd-t010.spec.toml` | BPGD, T=10, R defaults to code length | Figure 3 |
| `bpgd-t070.spec.toml` | BPGD, T=70, R defaults to code length | Figure 3 |
| `bpgd-t100.spec.toml` | BPGD, T=100, R defaults to code length | Figure 3 |
| `bpgd-t100-r002.spec.toml` | BPGD, T=100, R=2 | Figure 6 |
| `bpgd-t100-r005.spec.toml` | BPGD, T=100, R=5 | Figure 6 |
| `bpgd-t100-r010.spec.toml` | BPGD, T=100, R=10 | Figure 6 |
| `bpgd-t100-r050.spec.toml` | BPGD, T=100, R=50 | Figure 6 |
| `bpgd-t100-r882.spec.toml` | BPGD, T=100, R=882 | Figure 6 |

`bpgd-t100` and `bpgd-t100-r882` resolve to the same round limit on B1 but retain separate figure identities. Their policy composition may share numerical evidence after exact source settings are checked.

## Policy and experiment inventory

- Algorithm 1 uses binary sum-product BP, then chooses the most reliable undecimated variable after a failed round. The source fixes its prior to magnitude 25 with sign determined by the current marginal. Its zero-bias boundary differs between Algorithm 1 and Equation (36); the existing canonical controller declares an interpretation and must not be labeled bitwise source-exact.
- Code/noise: the paper's B1 `[[882,24,18 ≤ d ≤ 24]]` lifted-product CSS code under independent bit-flip noise. Figures 3 and 6 plot block error rate against physical bit-flip rate, approximately 0.04–0.10. Figure 3 states that each point was collected until 100 error cases. Figure 6's stopping and point coordinates must be transcribed before curve assessment.
- Candidate repository artifact: `data/artifacts/b1-panteleev-kalachev-v3.npz`, with project-derived logical basis. It is source-pinned to a Panteleev–Kalachev construction, but its **paper-experiment identity is not yet verified** for this figure.
- Circuits and detector/observable maps: not applicable to this selected binary code-capacity target.
- Published curve data and uncertainty: not yet digitized. No statistical tolerance, full denominator, or source settings manifest is frozen for these figures.

## Reproduction path

The [bounded B1 policy-file gate](../../../docs/css-literature-gate.md) exercises `bpgd-t100-r002.toml` on matched near-zero-noise samples for interface and provenance validation. Later bind this paper's ordered B1 artifact, noise grid, stopping/denominator rule, expected points, tolerance, environment, and ledger to a reproduction manifest. A cross-paper B1 or BB code run is a controlled adaptation unless it exactly matches this paper's experiment.
