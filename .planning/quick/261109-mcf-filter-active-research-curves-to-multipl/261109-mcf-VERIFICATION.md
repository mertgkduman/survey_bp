# Verification — passed

Implementation: `7eeddf7`.

- `.venv/bin/python -m bp_registry.research.cli build`: successful. Rebuilt catalog, contracts, package template, policy catalog and matrix previews are byte-identical to the initial checkout. The broad retained catalog is intentionally preserved; the shared JS active projection is reapplied after browser overlays.
- `.venv/bin/python -m pytest tests/research -q`: **118 passed in 27.34s**. Includes measurement validity, retirement, distinct rates, repeated cohorts, compatible multi-source curves, incompatible channel/kernel/sampling/evaluator evidence, zero-failure bounds, coordinate semantics, fixture aliases and rebuilt-catalog regression.
- `.venv/bin/python tests/research/browser_public_results.py --output .git/research-public-results-261109-mcf-final`: **7 browser workflow groups passed**, no page errors. Every remaining code's picker/table/CSV/settings agrees with the filtered collection; saved choices match provenance members. Empty view clears cards, exact saved mode, stale matrices and Stim, and download validation. Missing A5/B2 defaults fall back to an available input. Custom matrix/Stim validation, singleton/multi-rate overlay refresh, reload, fixture exclusion, mobile and v1 load pass. Synthetic overlays exercise display refresh only; they are not science evidence.
- `.venv/bin/python tests/research/browser_curves.py --url http://127.0.0.1:8876/web/research/ --output .git/research-public-curves-261109-mcf`: **7 existing browser groups passed**, no page errors. Labels, retirement, keyboard search, toggles, hover, CSV/receipts, independent cards and mobile controls remain functional.
- Real browser import separately reused two retained `.git/research-revision-browser-final/` result directories through unmodified `ResearchImport.read`: the one-rate Q-BPGD result stayed hidden (63 curves); the two-rate circuit result appeared (64 curves), persisted after reload, and added only its eligible circuit choice. No new worker or simulation was invoked for browser verification. See `retained-browser-import-check.json`.
- `node --check` for both edited JS modules and `git diff --check`: pass.
- `preservation-check.json`: hashes and direct byte comparisons for archived v1 and all generated catalog/template/contract/policy/matrix files; no raw data, experiment registry or model-config changes. No retained campaign was rerun. The unit suite uses bounded temporary test fixtures.

The original browser_v2/browser_revision integration scripts were updated for hidden singleton circuits and imports; their simulation-bearing end-to-end runs were not repeated. Coverage for this display task comes from the two no-simulation browser workflows and retained-result import check above.

## Scope and counts

Before: 105 projected curves, 361 points, 7 public codes, 3 registered circuits.
After: 63 projected curves, 319 points, 6 public codes, 0 registered circuits.
All 42 removed curves contain one distinct measured rate. See `REMOVED-FROM-ACTIVE-VIEW.md` and `active-view-audit.json` for their IDs, labels, input, datasets, source-series IDs and rates. Hidden input identities: GB46, relay-surface-d3, relay-bb144-memory-z, beamsearch-bb144-memory-z-p005. The internal three-qubit fixture was already absent from active examples/catalog; both registered aliases are now centrally excluded on import as well.
