# PriorTilt Fig. 1: source contract and canonical campaign

[Ye and Delfosse, PriorTilt (arXiv:2611.13373v1)](https://arxiv.org/html/2611.13373v1) tests sparse BP-prior perturbations against RelayBP-1 and beam search. It directly fits the project's BP-internal policy focus. Its circuit experiments are an explicitly scoped reproduction task, without closing or reordering the existing CSS/Pauli/circuit publication gates.

The pinned [author artifact](https://github.com/ionq-publications/PriorTiltDecoder) provides exact circuits, released counts, and full-precision three-phase schedules. `source.json` contains commits, hashes, source licenses and settings. Preserve `SOURCE-LICENSE` (CC-BY-NC-SA 4.0) with these author artifacts; our independently written mathematical policy calls the existing canonical min-sum sweep. Source code archives are reference evidence, not a replacement BP kernel. The Beam reference archive is separately pinned; Relay reference is v0.2.2, commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3` (Apache-2.0), already retained by earlier provenance records.

| Fig. 1 panel | Code | Cycles | Physical circuit rates | Circuit noise |
|---|---|---:|---|---|
| BB144 | [[144,12,12]] | 12 | .001, .002, .003, .004, .005 | Uniform Bravyi circuit model |
| BB70 | [[70,6,9]] | 9 | .0005, .0008, .001, .002 | Released moving-qubit model, no leakage/loss |
| GB102 | [[102,22,9]] | 9 | .0005, .0008, .001, .002 | Released moving-qubit model, no leakage/loss |

Twenty-six exact X/Z memory circuits yield 39 plotted decoder/code/rate points. XYZ experiments in the repository are outside Fig. 1. `source_contract.py` independently checks all circuit hashes, one-to-one DEM mechanisms (no detector-only merge collisions), schedule/CSV agreement and the metric; `source-figure1.csv` and PNG/PDF reconstruct 39 author measurements from 78 basis rows without digitization.

- PriorTilt: 60 ordinary sweeps, then at most 3000 rounds of six sweeps; published three-phase schedules selected exactly by code/rate, without interpolation or tuning. Statistics include the final six initial sweeps, posterior and outgoing messages. Priors are replaced with original prior plus one round's offset; messages continue, offsets never accumulate.
- RelayBP-1: 80 initial sweeps then 300 additional 60-sweep legs, stopping at first convergence. Published per-code gamma settings; messages reset per leg while posterior memory carries over. All-failed return is the initial candidate.
- Beam: width 32, 40 initial sweeps, ten rounds of 30 sweeps **per path**; 340 is not the all-path work cap. Source degree filtering, root selection, ties, pruning and all-failed initial-candidate return are explicit. All discarded-path work is counted.

All use unchanged canonical float64 min-sum equations, unit scaling/no offset, no cap, source hard ties at zero. The canonical total-minus-excluded-message reduction differs from native prefix/suffix arithmetic and can amplify roundoff. This is a canonical adaptation with qualified policy semantics, not bitwise native replication. `qualification.json` records the numerical boundary; the initial failed strict-state probe is retained in spike 059. Deterministic indexed policy randomness differs from native RNG but preserves the declared distributions. Source reference constructors are isolated from the project environment.

The figure reports **(X-memory observable errors / X shots + Z-memory observable errors / Z shots) / cycles**. Nonconvergence is a separate recorded outcome, never automatically a logical failure. Each basis stops at **20 observable errors or 100,000,000 decoded shots**, retaining the exact prefix. This standing local stop rule has lower precision than the authors' often 100–500 errors/up to 1 billion shots; do not claim equivalent precision or superiority. Exact 97.5% capped inverse-binomial/binomial intervals for each basis are summed over cycles, yielding at least 95% simultaneous X/Z coverage. Source bars remain published 1σ.

Each of 39 Slurm array workers has **one CPU** and processes its X and Z bases sequentially/interleaved. All methods consume immutable shared bit-packed Stim batches per code/rate/basis. Noise generation has independent per-chunk seeds and saved bytes authoritative across SIMD variants; policy RNG uses independent method/basis/global-shot identities. Batching, resume order and worker completion cannot change inputs or policy draws. Qualification seeds are separate and never enter production.

`design.json` and `plan.json` freeze code, circuits, source counts, resolved lookup schedules, software versions, budgets, evaluation and seeds. Every committed columnar NPZ event ledger retains candidates, predictions, work, timing, path trace and offset/gamma hashes; its marker binds the shared original detector/observable batch. Marker publication is atomic and uncommitted chunks are regenerated. Workers checkpoint/requeue before wall time and stop resumably if free storage falls below 10 GiB. Data stay under ignored `results/`; raw evidence is never erased on completion. Instrumented controller timing excludes JIT warmup, sampling, independent evaluation, audit and I/O; includes Python admission and provenance work. Work means BP sweeps and actual directed updates across every executed path, with random draws and biased-node updates reported separately.

Each completed point is re-read by a fresh interpreter in the same one-CPU allocation. The audit independently parses original Stim error targets, checks **every** candidate against detector/observable equations and every trace against work/budgets, verifies immutable samples and stopping, and replays chunk endpoints. Only complete audited X/Z pairs enter `comparison.csv`, `RESULTS.md` and the overlay. Both original denominators are retained; there is no fictitious combined binomial denominator. Source comparisons use pointwise local intervals without a full-curve agreement claim. No existing public catalog or archived interface is changed by this campaign launcher.

From the repository root, with `PYTHONPATH=src` and `.venv/bin/python`:

```sh
python data/reproductions/priortilt-2611-13373/source_contract.py
python data/reproductions/priortilt-2611-13373/qualify.py
python data/reproductions/priortilt-2611-13373/run.py --freeze
python data/reproductions/priortilt-2611-13373/run.py --submit
python data/reproductions/priortilt-2611-13373/run.py --index 0 --audit
python data/reproductions/priortilt-2611-13373/run.py --collect
```

Native qualification build recipes: unpack `priortilt-source.tar.gz`, run `cargo build --release --manifest-path decoder/Cargo.toml`, expose `libpriortilt_rs.so` as `priortilt_rs.so` in an isolated module directory and set `PRIORTILT_REFERENCE`. Unpack `beam-source.tar.gz`, build `decoder/setup.py build_ext` with Cython 3.2.4 into an isolated directory and set `BEAM_REFERENCE`. Build/install Relay v0.2.2 separately and set `RELAY_REFERENCE`. No native binary is imported by campaign workers. Default qualification paths under `/tmp/survey-bp-*261113373` are local build artifacts, not committed dependencies.
