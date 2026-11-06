---
status: passed
quick_id: 261106-nd0
date: 2026-11-06
---

# Workbench revision verification

All requested workflow changes are implemented. Scientific Phase 11 gates and publication claims are unchanged.

## Executed checks

- 144 Python/Node-backed tests passed in 39.99 seconds: research catalog, display, projections, coordinate transforms, contracts, runner, export/import integrity, circuit adapter, resolution, study-cache API, and compiled quaternary/Q-BPGD regressions.
- 22 Playwright workflow groups passed without browser errors across three scripts: `browser_curves.py` (7), `browser_v2.py` (10), and `browser_revision.py` (5).
- Real downloads were extracted outside repository paths and executed through their shared runner. The composed Q-BPGD fixture used MS, damping 0.2, scale 0.8, offset 0.25, and Q8. The circuit fixture generated two distinct probability inputs and completed 2 and 3 shots, then passed verified browser import.
- Responsive views fit at 390px; keyboard searches, curve toggles/previews, visible-only details/exports, matrix changes, baseline presets, and KaTeX rendering were exercised.
- Rehashed false confidence/count/flag/marker metadata is rejected. Historical adaptive ledgers remain compatible. The archived v1 package still validates.
- `git diff --check` passed. No expensive scientific simulation campaign was launched.

Detailed commands and browser receipts: `261106-nd0-verification.json`. Local screenshots/packages/ledgers are in the named `.git/research-revision-*` directories, excluded from Git; these are implementation checks, not new performance datasets.

## Scientific acceptance

The independent review in `261106-nd0-SCIENTIFIC-REVIEW.md` closes all initial plan-check blockers. Q-BPGD keeps committed messages through fixation; an equivalent policy matches the frozen no-policy recurrence. Legacy aggregate caps and deterministic one-shot Stim prefix traversal are enforced. Circuit Type I/II is an explicitly local partition of observable failures, and mixed adaptive/fixed points retain their own uncertainty methods.

The results catalog restores three retained circuit CPU-profile curves at p=0.005 and T=8. They were omitted by a catalog gap and remain local mechanism/performance evidence, not paper reproductions. The older comparison report repeats the same samples and is provenance only.

Curve views retain source identities and seeds. Exact reused evidence is deduplicated; pooling requires known compatible implementation/settings and an explicit disjoint fixed-IID contract. Current catalog views contain no unproved pooling. Source transcriptions, retired code-capacity clipping curves, and the internal three-qubit fixture are absent from active result choices. Archived evidence is preserved.

## Limits

- Circuit portable execution supports the pinned plain SPA/MS adapter; unsupported intervention/precision combinations remain validation errors.
- Adaptive failure-stopped runs do not claim fixed-N confidence intervals.
- In all-target mode, shots is a target and may be exceeded; failure-only targets have no implicit shot cap. All-empty point settings are invalid.
- New simulations execute locally after download. Browser imports are local; persistent catalog additions use the CLI.

Preview: `http://127.0.0.1:8765/web/research/`. Reopen with `PYTHONPATH=src .git/research-interface-verify/bin/python -m bp_registry.research.cli serve --port 8765 --no-build` (or an installed repository environment).
