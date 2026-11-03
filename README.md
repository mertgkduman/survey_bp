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

The current implementation covers **binary CSS and correlated quaternary code-capacity decoding**, with a bounded CPU circuit-integration prototype:

- Versioned experiment manifests, immutable code artifacts, and independent
  algebraic and recovery checks.
- Canonical sum-product, min-sum, normalized min-sum, and offset min-sum updates,
  with explicit compatibility rules for flooding and local schedules.
- Scheduling policies, typed work budgets, event ledgers, and run verification.
- A native `ldpc.BpDecoder` baseline and source-linked memory/Relay BP work.
- A separate four-state Pauli BP kernel and Phase 11 quaternary mechanism and assessment records.
- Pinned Relay-BP and BeamSearch Stim circuit fixtures and an opt-in Sinter adapter for plain binary flooding SPA or min-sum on compatible independent-fault detector models.

The [current project state](.planning/STATE.md) is Phase 11 quaternary reproduction and comparisons. The circuit adapter is an integration and throughput pilot; paper-specific circuit models, policy compatibility, native references, and reproduction assessments remain Phase 12–13 work. See the [circuit kernel guide](docs/circuit-kernel.md) for exact scope and measurements.

All three regimes remain in the intended journal-paper scope. BP-internal
modifications take priority over substantial optional OSD/LSD postprocessing.

## Installation

The [research interface](docs/research-interface.md) provides paper/study browsing,
interactive retained results, decoder and code libraries, and downloadable local
experiment packages. After installation with `.[performance,circuit,analysis]`,
start it with `.venv/bin/python -m bp_registry.research.cli serve --port 8765`
and open **http://127.0.0.1:8765/web/research/**. New simulations execute locally
after download. The browser and terminal exporter share the catalog and strict
experiment contract; historical evidence remains in its original directories.

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

For the optional Stim/Sinter circuit adapter and compiled CPU kernel, install `.[circuit]`.

The currently qualified HPC development environment is documented in
[environment-pins.md](docs/environment-pins.md). A new installation must pass
manifest preflight; it does not automatically inherit that environment's
qualification. When using an existing qualified environment, retain its pinned
dependencies and follow the environment guide.

## Run a small checked experiment

For the researcher-facing one-command workflow, supply a study and a TOML decoder file:

```bash
bp-registry data/studies/fair-beam-relay-css-v2.json \
  --decoder examples/bb72-relay-decoder.toml --workers 8
```

The command verifies and reuses the published BB72 package when present, or produces and verifies it when absent. For a custom composition of registered canonical CSS policies, use `OMP_NUM_THREADS=1 bp-registry examples/three-qubit-study.json --decoder examples/three-qubit-decoder.toml`. Python users can import `ensure_study` from `bp_registry.study`. See the [researcher study command](docs/researcher-study-command.md) for the file formats, result identity, and scope.

The [decoder-file guide](docs/decoder-files.md) explains where to place decoder
files, how their policy fields are interpreted, and how a reproduction freezes
them. The [Yao vanilla BP study](data/reproductions/yao-2312-10950-vanilla/README.md)
contains four named binary/BP4 v1/v2 files and matched A5/B2 code-capacity runs.

Run these commands from the repository root. The example uses a deterministic,
two-shot, three-qubit CSS development fixture and writes to a fresh temporary
directory:

New plain flooding binary SPA and BP4 decoders default to the float64 v2
numerical profiles. See the [profile guide](docs/numerical-profiles.md), the
[side-by-side HTML](docs/decoder-numerics-v1-v2.html), and the matching
[PDF](docs/decoder-numerics-v1-v2.pdf). The checked fixture below retains its
explicit historical v1 profile. New v2 manifest examples are
[`canonical-v2-default.json`](examples/canonical-v2-default.json) and
[`quaternary-v2-default.json`](examples/quaternary-v2-default.json).
Compiled BP4 min-sum selected with `rule="min_sum"` now uses the corrected
int8 scalar-message policy. Binary and BP4 compiled flooding graphs accept a
shared, explicit `BpFloodingPolicy` for float16/32/64 or signed fixed 8/16/32
resolution, message scope, and optional coefficient rounding. The
[resolution contract](docs/numerical-profiles.md#composable-flooding-resolution)
specifies the exact boundaries and publication-status limit.

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
| [`data/circuits/`](data/circuits/) | Pinned source circuit archives and representative Stim fixtures |
| [`data/manifests/`](data/manifests/) | Experiment configurations and schema snapshots |
| [`data/evidence/`](data/evidence/) | Source, protocol, and artifact provenance |
| [`literature_policies/`](literature_policies/) | Per-paper source specifications, qualified decoder TOML files, and the [cross-regime paper index](literature_policies/PAPERS.md) |
| [`data/results/`](data/results/) | Retained development and pilot evidence |
| [`docs/`](docs/) | Technical guides, source decisions, and development reports |
| [`scripts/`](scripts/) | Campaign and analysis utilities |
| [`.planning/`](.planning/) | Project scope, roadmap, phase plans, and execution records |

Further reading:

- [Git workflow and archived branch recovery](docs/git-workflow.md)
- [Study-design glossary and status key](docs/study-design-glossary.md) ([PDF](docs/study-design-glossary.pdf))
- [29 September development update](docs/development-update-20260929.md) ([PDF](docs/development-update-20260929.pdf))
- [Native CSS pilot guide](docs/phase1-pilot.md)
- [Memory-policy source decisions](docs/memory-policy-sources.md)
- [Profiling and tracing strategy](docs/profiling-and-tracing-strategy.md)
- [Research novelty and depth register](docs/research-novelty-and-depth-register.md)
- [Project roadmap](.planning/ROADMAP.md) and [current state](.planning/STATE.md)

The project is research software under development. A distribution license has
not yet been selected.
