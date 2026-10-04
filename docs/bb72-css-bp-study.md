# BB72 CSS BP comparison v1

The frozen [study design](../data/studies/bb72-css-bp-v1.json) defines a small-code controlled comparison on the source-pinned Bravyi `[[72,12,6]]` bivariate bicycle matrices. This is independent-X, perfect-syndrome **code-capacity** decoding. The code's distance of six is source-reported; the project's ordered logical basis is derived and algebraically checked, not shown equivalent row by row to the author's basis. Neither the original Bravyi circuit simulation nor any BP paper curve is reproduced by these runs.

## Decoder cohort and compatibility

| Family | Parameters screened on selection samples | Comparison role | Qualification |
| --- | --- | --- | --- |
| Sum-product BP (SPA) | V2C fresh-message weight `γ ∈ {1, 0.75, 0.5}` | Fixed `γ=1` reference; one selected SPA variant | Canonical binary BP baseline; damping equation transplanted from an erasure study |
| Min-sum BP (MS) | `γ ∈ {1, 0.5}` | Selected MS variant | Canonical update adaptation |
| Normalized min-sum (NMS) | `α ∈ {0.7, 0.85}` × `γ ∈ {1, 0.5}` | Selected NMS variant | Canonical update adaptation |
| Offset min-sum (OMS) | offset `β ∈ {0.1, 0.2}` × `γ ∈ {1, 0.5}` | Selected OMS variant | Canonical update adaptation |
| BP guided decimation (BPGD) | 8 rounds × 5 sweeps; `γ ∈ {1, 0.5}` | Selected intervention variant | Yao *et al.* Algorithm 1 interpretation transplanted to BB72 with a smaller cap |
| BP syndrome flip (BP-SF) | 20 baseline sweeps, at most four weight-one tests of five sweeps; `γ ∈ {1, 0.5}` | Selected intervention variant | Source-linked controlled CSS adaptation with deterministic seeded order |

All arms use the same flooding schedule, numerical profile appropriate to the update rule, pinned BB72 artifact, bit-flip channel, all-terminal denominator, at most 40 BP sweeps per physical sample, and at most 8,640 messages per direction. BPGD and BP-SF may do extra branching, ranking, transforms, or checks. Their typed work and BP calls are therefore reported separately; the shared edge cap does **not** assert equal total CPU cost. Incompatible combinations fail public preflight.

The damping recurrence is `m_next=(1−γ)m_previous_committed+γm_fresh`, reset at each new attempt. `γ=1` is the undamped control. The source [damping equation](https://arxiv.org/html/2411.08177v2#S4.SS2) was studied on erasures; these bit-flip applications are adaptations. [Yao *et al.*](https://arxiv.org/html/2312.10950v2) studied BPGD on B1 at different sweep and round settings. [BP-SF](https://arxiv.org/html/2507.00254v1) uses different parallel selection behavior. The [Bravyi source repository](https://github.com/sbravyi/BivariateBicycleCodes/tree/fa77e3333d3ec44c79d8f914dd24c040d1da471b) uses circuit-level BP-OSD for its original experiment. `source_settings_view` records these distinctions beside the controlled results; it is not a second set of faithful BB72 CSS curves.

## Sampling and assessment

Three X-error rates, `p ∈ {0.03, 0.05, 0.08}`, are fixed before sampling. Every candidate at a rate sees the same 128 selection samples. Selection and evaluation have different physical-sample identities and seeds. Within each family, the candidate with the fewest unconditional failures pooled equally across all three selection rates advances; ties use fewer check-to-variable updates, then stable configuration ID. The fixed undamped SPA reference advances regardless of selection.

Each selected candidate and the fixed reference then receives **512 new matched physical samples per rate**. An unconditional failure is every terminal outcome other than exact or stabilizer-equivalent recovery. Timeout, nonconvergence, unavailable output, invalid syndrome, and logical failure stay in the 512-shot denominator. The study uses fixed shots with no outcome-dependent stopping.

The report gives exact 95% Clopper–Pearson intervals for each failure fraction, paired newly/lost valid counts, two-sided exact McNemar tests, and Holm adjustment over the selected family-by-rate contrasts. The prespecified marginal-rate interval half-width target is 4.5 percentage points, met by 512 fixed shots even at the widest exact interval. This sample size does not guarantee power for a small paired difference. A directional difference is recorded only at adjusted `p ≤ 0.05` with the matching observed sign. An inconclusive contrast remains inconclusive; a result at one BB72 rate does not rank decoders generally. Raw outcome classes, terminations, typed work, and runtime/convergence availability are retained. The primary comparison is **within this controlled CSS study**; source-paper reproduction has its own separate status.

## Execution and evidence gates

The design was committed before study sampling. A run seal hashes the design, canonical source tree, manifest templates, and runner. Generated manifests are write-once. Every arm is run through public canonical execution and replay-verified; group verification checks exact sample identities before selection or evaluation analysis. An existing ledger without its seal, a changed source file, a changed manifest, an incomplete arm, or overlap between selection and evaluation blocks reporting.

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py preflight-selection
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py run-selection --workers 32
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py freeze-selection
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py preflight-evaluation
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py run-evaluation --workers 18
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_css_study.py report
.venv/bin/python scripts/render_bb72_css_study.py
.venv/bin/python scripts/package_bb72_css_study.py
```

Run in a bounded Slurm allocation when local CPUs are insufficient. Outputs are under `data/results/bb72-css-bp-v1/`: per-arm `manifest.json`, `events.jsonl`, and `result.json`, plus `seal.json`, `selection-lock.json`, aggregate `result.json`, `REPORT.md`, and read-only offline `study.html`. The package step verifies every raw ledger and writes deterministic `events.jsonl.gz` copies plus `publication-manifest.json` for GitHub; uncompressed ledgers remain on the HPC filesystem for replay.
