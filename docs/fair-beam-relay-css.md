# Fair initial BP with BeamSearch and RelayBP extensions

This controlled CSS implementation compares two ways to spend BP work after one identical min-sum flooding run. It is a **source-informed adaptation**, not a reproduction of either paper's circuit-level experiment. The fixed eight-shot BB72 example is an implementation fixture marked `not_assessed`; its outcome counts do not rank decoders.

## Common initial stage

For each X-only physical sample and each damping level, both extensions receive the same Z-check syndrome and the *same in-memory* initial BP result. The fixture runs both `gamma=1.0` (off) and `gamma=0.5` (on) on the same physical shot IDs. The initial stage uses the canonical float64 min-sum update, flooding schedule, channel LLR prior, 20-iteration cap, and V2C damping

\[
 m_{v\to c}^{(t+1)}=(1-\gamma)m_{v\to c}^{(t)}+\gamma\,\widehat m_{v\to c}^{(t+1)},\qquad \gamma=0.5.
\]

Here `gamma` is the fresh-message coefficient. `gamma=1.0` is the undamped control. If initial BP finds an original-syndrome-valid correction, both methods stop with that exact correction and zero additional units. Runtime and typed work for the initial run are recorded separately from the extensions.

## Additional units

| Method | One counted additional unit | State crossing from its predecessor | Other state |
|---|---|---|---|
| RelayBP | A disordered-memory DMem-BP run | Final posterior LLRs only | Messages and damping reset to channel priors; a fresh seeded per-variable memory-strength vector is drawn. |
| BeamSearch | One 0 or 1 decimated child branch | Surviving V2C messages and posterior for warm start | Fixed variables are removed from BP, syndrome is adjusted, and a separate damping history begins from the inherited messages. |

Relay's source memory coefficient is distinct from V2C damping. For each variable and each Relay extra leg, the effective prior is

\[
 \Lambda_j^{(t)}=(1-g_j)\Lambda_j^{\mathrm{channel}}+g_j M_j^{(t-1)}.
\]

Within each damping level, the fixture declares independent uniform `g_j` draws in `[-0.24, 0.66]` with a deterministic per-shot/per-leg PCG64 seed. That interval is an exploratory port of a source circuit setting to BB72 CSS; it is not selected from this fixture's evaluation outcomes. The [RelayBP paper](https://arxiv.org/html/2506.01779v2) calls its *first memory-BP run* leg 0. This controlled study instead separates a shared plain-BP initial stage and counts **only subsequent disordered-memory runs** as Relay extra legs.

BeamSearch chooses the unmasked variable with the smallest absolute cumulative posterior LLR, branches on 0 and 1, excludes fixed variables from masked min-sum BP, and ranks surviving paths by summed absolute cumulative LLR. It retains pruned and budget-denied branches. This follows the [BeamSearch paper's](https://arxiv.org/html/2512.07057v2) algorithmic shape with a CSS problem and added damping; it does not claim to reproduce the pinned C++ edge-case behavior.

Both extensions use the same ceiling on *additional* check-to-variable updates. Their realized work may differ because they stop early and a masked branch has fewer graph edges. The ledger reports initial work, extra work, each attempted unit, observed serial runtime, final candidate, and independent original-problem outcome. A count of units is not a compute-equivalent comparison.

## Reproduce the development fixture

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/run_fair_beam_relay_css.py run \
  --design data/studies/fair-beam-relay-css-v1.json \
  --output data/results/fair-beam-relay-css-v1-smoke
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/run_fair_beam_relay_css.py verify \
  --design data/studies/fair-beam-relay-css-v1.json \
  --output data/results/fair-beam-relay-css-v1-smoke
```

`verify` resamples each declared shot, reruns both extensions, checks every deterministic ledger field, and binds the result to the design, ledger, and hashes of the controller and runner files. Other imported canonical modules are verified by replay but are not individually hashed in this result. Observed runtime is checked for type and method but is not compared bitwise. The decoder receives only the syndrome; the independent evaluator receives the hidden physical error afterward.

A statistical BB72 study needs a new prespecified selection/evaluation split, several noise points, power/precision target, and separate source-configuration and shared-work analyses. These eight development shots are not that study.
