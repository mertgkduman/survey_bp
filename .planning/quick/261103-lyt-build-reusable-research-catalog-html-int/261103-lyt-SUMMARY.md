---
status: complete
date: 2026-11-03
mode: autonomous
scientific_phase_status_changed: false
---

# Research workbench and portable experiments

Delivered a repository-hostable static workbench at `web/research/` and the
`bp-registry-research` CLI. The initial real catalog contains 10 paper/local-study
records, 14 experiments/datasets, 121 result series, 519 plotted observations,
8 code records, 3 source circuits, and 4 explicitly defined noise models.
Historical evidence remains in its original directories with original identities.

## Implementation

- Shared machine-readable source/input registries, relationship validation,
  additive normalized catalog extensions, and read-only legacy study adapters.
  Pilot/confirmation, source/canonical, weighted/binomial, and local/downloadable
  evidence remain distinct. Float64 presentation-study BP4 arms have their actual
  runner damping overrides, not inherited Q8 source settings.
- Responsive HTML paper/result/specification/code/noise/circuit browsing, real
  SVG plots/tables, keyboard point inspection, exact source-file and effective
  configuration receipts, and browser ZIP export.
- Versioned portable experiment admission over existing policy/resolution
  definitions and actual compiled kernels/evaluators. Binary CSS, joint Pauli,
  Q-BPGD, and plain Stim/Sinter decoding retain their separate semantics.
- Custom CSS and Stim inputs, physical p versus decoder p0, explicit physical
  Pauli tables, seeded paired samples including code identity, computational
  caps, immutable outputs, full effective settings, implementation/input hashes,
  durable per-shot ledgers, partial-run status, summaries, uncertainty and plots.
- Python and browser share package templates. Exported code imports repository
  implementations. Original registered study ZIPs use `ensure_study`, with exact
  input hashes and validation-only mode; no large campaign was started.
- Installation/preview/extension/testing guide at `docs/research-interface.md`.

## Verification

83 appropriate Python checks passed in 23.09 seconds: new research contracts,
exporters/runners/catalog plus existing circuit, resolution-policy, and study-API
regressions. GSD specialists audited catalog science and execution semantics;
confirmed admission, provenance, timing, stopping, and effective-policy issues
were fixed and covered by regressions.

Actual Chromium verified the requested workflow set, including selectors changing
plot geometry/tables, byte-exact frozen export, imported undamped BP4 policy,
custom noncommuting input rejection, four downloaded packages executed after
relocation, unsupported circuit policy rejection, exact original registered
workflow validation, receipt overrides, keyboard plot interaction, and all six
mobile views. Each generated binary/BP4/custom-circuit/source-circuit package ran
four shots, generated a plot, and refused overwrite. Total browser smoke sampling
was 16 shots, unrelated to any performance claim.

See `261103-lyt-VERIFICATION.json` for inspectable checks, tiny result rows,
identities, commands, and limits. Full local screenshots, ZIPs, raw ledgers, and
execution logs are under `.git/research-interface-browser-release/` and can be
regenerated with the committed browser verification script. The separate testing
venv used existing installed scientific dependencies; a fresh network installation
and non-Chromium/screen-reader tests were not run.

## Use and extension

Run `python -m bp_registry.research.cli serve --port 8765` in the installed
environment, then open `http://127.0.0.1:8765/web/research/`. The delivered preview
runs in `.git/research-interface-verify`; use SSH forwarding for remote HPC access.
New simulations execute locally after package download.

Add paper/dataset evidence as a normalized `research-catalog-extension-v1` JSON,
register its path in `research/catalog/sources.json`, and rebuild the catalog.
Reusable code/circuit/noise records live in `inputs.json`. A new constructor or
algorithm needs an implementation resolver; adding evidence does not require
rewriting the HTML. External raw storage is represented by instructions and a
declared, unverified checksum without an invented download URL.

No core decoder kernel or scientific phase gate was changed. No campaign,
remote deployment, or raw-data relocation was performed.
