# Policy-Based BP Research Platform for QLDPC Decoding

`survey_bp` is a research platform for belief-propagation (BP) decoding of quantum
low-density parity-check (QLDPC) codes. It combines a systematic literature mapping
study, an executable experiment registry, and canonical decoding engines that
express compatible algorithms through explicit modular policies.

The aim is to make decoder differences interpretable, reproducible, and fairly
comparable, with every measured result linked to its configuration and evidence.
Native implementations serve as executable references alongside the canonical
engines.

## Current status

The current implementation focuses on **binary CSS code-capacity decoding**:

- Versioned experiment manifests, immutable code artifacts, and independent
  algebraic and recovery checks.
- Canonical sum-product, min-sum, normalized min-sum, and offset min-sum updates,
  with explicit compatibility rules for flooding and local schedules.
- Scheduling policies, typed work budgets, event ledgers, and run verification.
- A native `ldpc.BpDecoder` baseline and source-linked memory/Relay BP work.

Memory and Relay BP qualification is in progress. The default branch preserves
the source used by the ongoing calibration campaign; additional implementation
and diagnostic work is maintained on
[`gsd/phase4-memory-integration-20260926`](https://github.com/mertgkduman/survey_bp/tree/gsd/phase4-memory-integration-20260926).
See the [execution record](.planning/phases/04-memory-policies-and-relay-bp/04-EXECUTION-CONTINUATION-20260927-RESUMED.md)
for its validation and remaining gates.

Correlated quaternary code-capacity and circuit-level decoding are planned next.
All three regimes remain in the intended journal-paper scope. BP-internal
modifications take priority over substantial optional OSD/LSD postprocessing.

## Installation

The package requires **Python 3.12 or newer**. Exact runtime dependency versions
are declared in [pyproject.toml](pyproject.toml). From a fresh checkout, create a
development environment:

```bash
git clone git@github.com:mertgkduman/survey_bp.git
cd survey_bp
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip install pytest
```

Optional notebook and plotting dependencies:

```bash
.venv/bin/python -m pip install -e '.[analysis]'
```

The currently qualified HPC development environment is documented in
[environment-pins.md](docs/environment-pins.md). A new installation must pass
manifest preflight; it does not automatically inherit that environment's
qualification. When using an existing qualified environment, retain its pinned
dependencies and follow the environment guide.

## Run a small checked experiment

Run these commands from the repository root. The example uses a deterministic,
two-shot, three-qubit CSS development fixture and writes to a fresh temporary
directory:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight \
  data/manifests/canonical-three-qubit-development.json

OUT="$(mktemp -d "${TMPDIR:-/tmp}/canonical-three-qubit-development.XXXXXX")"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli canonical \
  data/manifests/canonical-three-qubit-development.json --output "$OUT"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli reconcile "$OUT/events.jsonl"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run "$OUT"
```

The run and verification reports should contain `final_row_count: 2`.
The fixture is explicitly marked `development_fixture` and `not_assessed`; it
checks execution and evidence semantics rather than statistical performance.
The [canonical engine guide](docs/canonical-engine.md) explains the numerical
conventions, policy contracts, expected outcomes, and ledger fields.

Inspect a retained checked result without generating new samples:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run \
  data/results/canonical-three-qubit-development
.venv/bin/python -m bp_registry.cli --help
```

Run the regression suite in a qualified development environment:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q
```

## Evidence and comparison rules

Every simulation emits an event ledger. Manifests identify code artifacts,
noise models, policy compositions, numerical conventions, budgets, and evidence
status. Independent evaluators judge recoveries against the original problem;
decoder policies cannot inspect hidden simulation truth.

Source-faithful reproductions, canonical adaptations, controlled comparisons,
and mapped-only literature evidence have distinct identities. Development
fixtures and pilot adaptations are not statistically verified paper
reproductions. Publication campaigns require prespecified tolerances, stopping
rules, denominators, and compute budgets, with failed or inconclusive evidence
retained.

## Repository guide

| Path | Contents |
| --- | --- |
| [`src/bp_registry/`](src/bp_registry/) | Registry, manifests, canonical engines, native references, and CLI |
| [`tests/`](tests/) | Algebra, policy semantics, execution, and provenance checks |
| [`data/artifacts/`](data/artifacts/) | Code artifacts and their identities |
| [`data/manifests/`](data/manifests/) | Experiment configurations and schema snapshots |
| [`data/evidence/`](data/evidence/) | Source, protocol, and artifact provenance |
| [`data/results/`](data/results/) | Retained development and pilot evidence |
| [`docs/`](docs/) | Technical guides, source decisions, and development reports |
| [`scripts/`](scripts/) | Campaign and analysis utilities |
| [`.planning/`](.planning/) | Project scope, roadmap, phase plans, and execution records |

Further reading:

- [Native CSS pilot guide](docs/phase1-pilot.md)
- [Memory-policy source decisions](docs/memory-policy-sources.md)
- [Profiling and tracing strategy](docs/profiling-and-tracing-strategy.md)
- [Research novelty and depth register](docs/research-novelty-and-depth-register.md)
- [Project roadmap](.planning/ROADMAP.md) and [current state](.planning/STATE.md)

The project is research software under development. A distribution license has
not yet been selected.
