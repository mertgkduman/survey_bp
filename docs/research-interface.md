# Research interface v2 and experiment packages

The v2 workbench in [`web/research/`](../web/research/index.html) views measured
results, compares code/circuit and decoder selections, and exports new experiments.
Paper and dataset browsing remains in the [v1 archive](../web/research/v1/index.html). It runs as static HTML/CSS/JavaScript. Catalog inspection, plots, CSV
downloads, and ZIP preparation happen in the browser. New simulations execute
locally after download.

## V2 workflow

V2 is the default at `/web/research/`. The earlier interface is preserved at
`/web/research/v1/`, including its frozen static catalog and package templates.
The sidebar opens on Getting started, followed by Available experiment results,
Experiment builder, Version difference and Recommendations, and Policies.

Results use **Code/circuit** and **Decoder** selectors. Each saved decoder ID
includes its original experiment context; selecting only an algorithm name would
not identify prior, cap, precision, or sampling cohort. Add plot creates independent
selections, curves, tables, CSV exports, and configuration receipts. Only locally
measured points appear in v2: source transcriptions and unmeasured coordinates
remain in v1/the source catalog. Importance estimates keep their declared
estimator and raw proposal-count semantics. Work/runtime units are not silently
normalized across incompatible methods or machines.

The builder has decoder/policy and code/circuit columns, followed by simulation
settings. Saved vanilla SPA specifications can populate editable controls;
study-specific procedures retain their original runner and display a compatibility
error rather than becoming plain BP. Matrix representations, row ordering, and
logical basis remain part of input identity. The complete JSON path preserves
custom settings that do not have visual controls.

Optional `sampling.stop_failures`, `stop_type_i`, and `stop_type_ii` stop each
rate point at the first reached target or its shot cap. They are positive integers
or null; old specifications with only seed/start/shots keep their behavior.
Circuit experiments accept observable-failure targets and reject Type I/II targets.
Adaptive runs record actual denominators and terminal reason, and leave confidence
bounds unavailable (`unavailable_optional_stopping`) rather than claim fixed-N
coverage. `budgets.max_shots` still bounds the whole planned sweep.

### Upload results

A completed portable run emits derived `catalog-entry.json` alongside its
manifest-bound evidence. Browser import reconstructs catalog records from the
bound files and ignores the derived entry, so edits to that convenience JSON
cannot change a displayed result. In Getting started, select these output files together:

- `result-manifest.json` (`catalog-entry.json` is optional and ignored);
- `requested-spec.json`, `effective-spec.json`, `run-manifest.json`, `status.json`;
- `events.jsonl`, `summary.json`, and `summary.csv`.

The browser verifies hashes and summary/ledger counts before adding a local
catalog overlay. Entries survive reload in browser storage. A naked catalog
entry, partial run, modified bytes, or conflicting identity is rejected. Browser
uploads are limited to 100 MB and browser-storage quota; use the CLI for larger
runs. Browser-local import does not write to the repository or a remote server.

For persistent repository registration:

```bash
# Run in the installed repository environment; supply the existing result folder.
bp-registry-research import-results /path/to/experiment/results
bp-registry-research build
```

This validates the completed output, writes a normalized JSON under
`research/imported/`, and registers its path in `research/catalog/sources.json`.
Raw data remains in the original output folder with hashes and storage instructions.
Review/commit the new index and generated catalog to share it; raw ledgers are
never presented as Git downloads merely because they exist locally.

Policies are defined in `research/catalog/policies.json`; equations are rendered
with vendored KaTeX and do not require a CDN. Named recent methods include primary
paper links and explicit builder/study/circuit qualification. Version difference
and Recommendations keeps the material removed from the main workflow visible,
with separate suggestions for future shared ingestion and policy/circuit work.

## Open a local preview

From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[performance,circuit,analysis]'
.venv/bin/python -m bp_registry.research.cli serve --port 8765
```

Open **http://127.0.0.1:8765/web/research/**. The command rebuilds the static
catalog before serving. `--no-build` serves its checked-in snapshot. The preview
serves tracked repository assets and the interface; it disables directory
listings and private configuration paths. When running on a remote HPC host,
forward port 8765 over the SSH connection to open it on your computer.

The installed command is `bp-registry-research`. The interface can also be
hosted as static files at its repository-relative location, with its referenced
repository assets. No server API, CDN, account integration, or deployment is
required. Serve it over HTTP; browser file-URL restrictions can prevent JSON
loading when double-clicking `index.html`.

## Browse a registered result

Select a paper or local study, then an experiment, dataset, code, and decoder.
In v2, the initial result is the local A5 vanilla BP4 v2 curve. V1 retains the paper/experiment/dataset browsing path described below. Select a decoder to see
its frozen file and arm-specific effective settings. **Export exact
specification** downloads that source file byte for byte, including its original
JSON/TOML format. **Download effective configuration receipt** additionally binds the selected arm and any runner overrides to the source checksum; a shared source file alone may describe several arms. Configuration receipts, analysis scripts, summaries, and raw
ledgers are linked when registered and actually accessible.

The presentation parameter study is an unpublished local study. External
papers have separate records. Their registered scope distinguishes measured
adaptations, source transcriptions, and mapped/blocked work. A result directory
or matching numerical point does not confer source-faithful status.

Tables preserve sample counts, Type I/II outcomes where available, uncertainty,
work units, and timing boundaries. Type I is an inconsistent syndrome; Type II
is a consistent syndrome with a nontrivial logical residual. Exact and
stabilizer-equivalent recoveries succeed. Circuit results instead concern
observable prediction errors. Weighted importance estimates retain their
estimator, raw proposal counts, weighted uncertainty, and denominator semantics;
their rate is not reconstructed by dividing raw failures by raw draws.

Source curves are dashed. A triangle denotes a bound; it is not plotted as an
observed nonzero rate. Unknown source denominators and unavailable uncertainty
remain missing. Work plots require a common work unit. Timing values keep their
reported scope; they do not establish an across-machine speed comparison.

## Create a new experiment

The visual builder exposes compiled plain binary CSS BP, joint Pauli BP4, and
the existing v2 Q-BPGD path, with explicit physical probabilities, decoder prior,
sampling seed, rate sweep, and computational caps. Selecting a frozen
specification creates a **new** request with a parent reference; its historical
result remains attached to the original experiment. Unsupported study-specific
procedures keep their original entry points instead of being substituted by a
plain decoder.

The compiled custom route supports flooding, sum-product/min-sum, the actual
float64 v1/v2 profiles, and supported numerical overlays. Overlays reuse
`BpFloodingPolicy` and `ResolutionPolicy`: float16/32/64, signed fixed
8/16/32-bit resolution, rounding scope, scale, old-message damping weight,
normalized/offset min-sum coefficients, hard decisions, and explicit coefficient
rounding. They model values at declared boundaries with float64 intermediates;
they do not promise bit-packed storage or native low-precision arithmetic.
The existing implicit BP4 min-sum policy is recorded when selected. Q-BPGD
supports its persistent v2 path and rejects a resolution overlay. The shared
contract rejects unsupported schedules and policies.

Physical depolarizing noise samples I/X/Y/Z with probabilities
`(1-p,p/3,p/3,p/3)`. Binary decoders use separate `2*p0/3` component priors;
BP4 uses the joint depolarizing prior specified by `p0`. For X-only sampling,
binary uses Bernoulli `p0`; BP4's explicit depolarizing decoder prior remains a
separate inference choice. Following the same scalar p does not make those
different prior models equivalent. Explicit physical Pauli probability tables
are available through custom JSON. Decoder priors and physical sampling are
recorded separately.

`sampling.shots` applies to each point; `budgets.max_shots` bounds their total.
The binary iteration cap applies separately to each X/Z component, and reported component sweeps are summed. The BP4 cap counts joint sweeps. Q-BPGD rounds times sweeps per round must fit the total sweep cap. Stim skipped
prefix samples also consume the circuit shot budget. Start with small budgets
for validation. The retained study-specific campaign runners remain the route
for their prespecified large campaigns.

## Custom CSS input

Choose **Custom CSS matrices** and supply this JSON format (also usable in a
complete custom experiment):

```json
{
  "hx": [[1, 1, 0]],
  "hz": [[0, 0, 1]],
  "lx": [[1, 0, 0]],
  "lz": [[1, 1, 0]]
}
```

Matrices are binary integers. Both X and Z check families must be nonempty and contain no identity-only rows. For a zero-logical-qubit code, omit the logical pair. Checks have the same nonzero width and satisfy
`hx * hz.T = 0` over GF(2). Supply both logical matrices or neither. Supplied
logical rows must have shape `(k,n)`, commute with the opposite checks, and have
the declared identity pairing. Python uses the existing `CssCode.validate`
contract, and independently evaluates recovery even when logical matrices are
omitted. BP4 also validates graph checks and isolated qubits. Pauli persistence
uses **I=0, X=1, Y=2, Z=3**; X-check rows precede Z-check rows.

The browser consumes the Python-generated field sets, enums, defaults, and
policy constraints, performs structural/algebraic checks, and repeats validation
locally before sampling. Stim parsing, detector-model extraction, and the full
kernel boundary remain authoritative Python checks.

## Circuit experiments

Choose a pinned circuit or import `.stim` text. Its noise is embedded in that
input. The package invokes Stim sampling and the actual Sinter custom-decoder
interface using `CanonicalBpSinterDecoder`; it stores detector data, observable
truth/predictions, detector fit, observable failure, and work for each retained
shot. `decompose_errors=False`, the independent-mechanism DEM, little-endian
observable conventions, float64 v1, flooding, and the tie policy are explicit.

This adapter supports plain SPA and min-sum. Damping, alternative precision,
Relay, Beam, and other interventions are rejected for this circuit route.
Different circuit-noise settings require separate Stim inputs. See the
[circuit contract](circuit-kernel.md) for its scope and source-fidelity limits.

## Run a package or use the terminal

Each browser/terminal ZIP contains `experiment.json`, `decoder.json`, `run.py`,
`analyse.py`, installation requirements, instructions, a hash manifest, and
embedded custom code/circuit inputs. Registered built-in constructions may
resolve through the explicitly selected repository. Python exports materialize
registered inputs into portable data. Browser exports embed available matrix
JSON and Stim text and otherwise retain a registered constructor identifier.
The local run materializes it and records its actual identity.

```bash
bp-registry-research validate research/examples/code-capacity.json
bp-registry-research export research/examples/code-capacity.json --output /tmp/example.zip
# Extract the ZIP into a new directory, then use the installed environment:
/path/to/survey_bp/.venv/bin/python run.py --repo /path/to/survey_bp --validate-only
OMP_NUM_THREADS=1 /path/to/survey_bp/.venv/bin/python run.py \
  --repo /path/to/survey_bp --output ./results/run-001
/path/to/survey_bp/.venv/bin/python analyse.py ./results/run-001
```

`research/examples/circuit.json` is a bounded project-owned Stim/Sinter fixture.
The `--repo` option accepts a checkout from any directory, including paths with
spaces. Existing outputs and ZIP files are rejected. Edited package bytes fail
the package manifest: import/edit the specification and export a new package.

Runs retain requested/effective settings, input and implementation identities,
package versions, event ledgers, aggregate JSON/CSV, and result hashes. Changing
configuration or implementation changes the content-derived experiment ID.
Partial failures retain evidence and are not converted into ordinary decoder
failures. New fixed-N intervals use a named 95% Wilson procedure; they do not
inherit a source study's different statistical stopping rule. Decode timings
include lazy JIT compilation when not warmed and state their measurement scope.

For an original registered study, Results also offers **Download original
registered workflow**. Its ZIP contains the frozen study/decoder files and a
wrapper around `ensure_study`, with their original hashes. Use `--validate-only`
to check it without starting a campaign. The terminal equivalent is:

```bash
bp-registry-research export-registered fair-beam-relay-css-v2 --output /tmp/original.zip
```

The original `bp-registry` / `ensure_study` interface is unchanged. It remains
the verified-cache and registered CSS-policy/campaign route. These new portable
compiled experiments have their own versioned contract; source-specific frozen
files are not relabeled as inputs accepted by another runner.

## Add a paper or dataset

`research/catalog/inputs.json` supplies shared code IDs, noise-model definitions, aliases, execution
artifacts/constructors, and circuit paths for both Python and HTML. Add a CSS
artifact or a Stim record there to expose a reusable input. New constructor
algorithms need a resolver in `contracts.py`; the interface itself needs no edit.
Source circuit exports preserve the pinned upstream commit and license files.
The current builder imports vanilla SPA decoder files exactly; more complex
frozen procedures use their original registered/source-specific runner. An edited
configuration always becomes a separate experiment.

The catalog has stable paper, decoder, code, circuit, experiment, dataset, and
series IDs. `research/catalog/sources.json` indexes legacy study adapters without
moving original evidence. `catalog.schema.json` documents the normalized format;
`catalog_model.validate_catalog` checks relationships and unique series.

1. Add the paper metadata to the source registry or a normalized extension.
2. Keep reusable decoder/code definitions distinct from the experiment's sample
   and budget settings. Assign new IDs when scientific settings change.
3. Have the analysis produce normalized JSON with `schema` equal to
   `research-catalog-extension-v1`. It can contain `papers`, `decoders`, `codes`,
   `circuits`, `channels`, `experiments`, `datasets`, and `result_series` arrays in the same
   format as the generated catalog. A series references one dataset, code, and
   decoder and contains its measured `points`.
4. Register that JSON path in `sources.json`'s optional `normalized_catalogs`
   array. Rebuild with `bp-registry-research build`. No interface edit is needed.

Points use `x`, `y`, `n`, `failures`, `ci_low`, `ci_high`, `status`, `mean_work`,
`work_unit`, `mean_seconds`, and estimator-specific `metadata`. Unknown values
are null. Identify confidence level/method, denominator, runtime boundary, and
any importance weighting in metadata. Preserve separate pilot/evaluation
cohorts. Assets declare a path, label, and kind; download availability/checksums
are derived from actual tracked bytes. Untracked large data stays local with
storage instructions and a checksum, rather than a speculative URL. An asset
outside Git can declare `storage_path`, `storage_instructions`, and an optional
`sha256`. The catalog labels that checksum unverified and supplies no download
URL; it does not scan a large external archive during a build.

Existing formats have read-only adapters in `catalog.py`. A new format can use a
small adapter or emit the normalized format directly. Presentation transcriptions,
canonical adaptations, and source-faithful reproductions retain separate labels.

## Verify the interface

```bash
PYTHONPATH=src:. OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/research
```

The legacy `browser_workflows.py` script exercises the v1 archive. V2 has a separate end-to-end check:

```bash
PYTHONPATH=src:. OMP_NUM_THREADS=1 python tests/research/browser_v2.py \
  --output /tmp/new-v2-verification
```

Optional browser verification uses Playwright in a separate testing environment:

```bash
python -m pip install playwright
python -m playwright install chromium
PYTHONPATH=src:. OMP_NUM_THREADS=1 python tests/research/browser_workflows.py \
  --url http://127.0.0.1:8765/web/research/ --output /tmp/new-interface-verification
```

That check exercises real retained data, selector changes, exact-file export,
custom input rejection, browser ZIP generation, tiny binary/BP4/custom and registered circuit runs, original-workflow hash validation,
analysis, overwrite refusal, keyboard focus, and desktop/mobile layout. It
creates local verification artifacts and does not launch a paper campaign.
