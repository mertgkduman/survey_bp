# Inspection and implementation boundaries

Inspected before choosing adapters: repository AGENTS/README, PROJECT/STATE,
Phase 11 plans, `study.py`/`study_cli.py` and `ensure_study`, decoder TOML/JSON
contracts and cross-rule checks, `resolution.py`, binary and quaternary
numerical profiles and compiled graphs, CSS constructors/artifacts, independent
CSS/Pauli evaluators, `circuit/sinter_adapter.py`, circuit tests, and retained
presentation/Yao/BB72 studies and their analysis/receipt/raw-ledger files.

## Established behavior

- `bp-registry` and `ensure_study` are an existing registered study execution and
  verified-cache route. They do not accept every historical diagnostic runner's
  decoder JSON. Preserve that interface; package original registered studies
  through the existing API.
- Binary CSS and joint Pauli kernels have distinct input, prior, stopping, and
  numerical contracts. Reuse compiled graphs and independent evaluators. Keep
  historical float64 v1 and canonical v2 identities intact. Numerical overlays
  use existing `BpFloodingPolicy`/`ResolutionPolicy` boundary rounding, with
  float64 intermediates; no claim of native low-precision arithmetic.
- Canonical v2 profiles include old-V2C damping 0.1. A frozen undamped arm must
  explicitly override it. BP4 min-sum has an implicit corrected Q8 policy that
  must appear in effective settings. Unsupported combinations fail before
  sampling. Q-BPGD uses the existing persistent graph method and a bounded
  rounds-times-sweeps budget.
- The actual Sinter adapter accepts historical v1 plain flooding SPA/MS on an
  independent-mechanism detector model. Detector fit and observable success are
  distinct. No circuit damping/quantization/Relay substitution is supported.
- Retained evidence mixes source transcriptions, small pilots, confirmation
  cohorts, canonical adaptations, fairness comparisons, weighted importance
  estimates, and controlled local baselines. These cannot be pooled or assigned
  a common source-faithfulness label. Raw proposal counts are not weighted-rate
  denominators. Pilot and confirmation settings need separate IDs.
- Git tracking, file existence, and external storage availability are different
  facts. Download links bind tracked bytes/checksums; local/external declarations
  do not imply accessible downloads. Evidence directories remain in place.

## Chosen product structure

`research/catalog/sources.json` indexes study adapters; `inputs.json` shares
code/circuit identifiers and artifacts across CLI and HTML. Additive normalized
JSON extensions register new papers/datasets without interface changes. The
static workbench consumes generated catalog, validation constraints, and the
same package template as the Python exporter.

The custom runner has its own versioned experiment contract rather than
relabeling source-specific policy files. It samples through the existing joint
Pauli sampler (decoder-neutral paired sample IDs including code identity), calls
the shared kernels, and independently evaluates outcomes. It streams per-shot
JSONL, preserves interrupted-run evidence, hashes effective settings/input/
implementation/environment, and refuses existing outputs. Exported scripts
import this implementation instead of copying decoder algorithms.

No expensive scientific campaign or remote deployment belongs to this task.
