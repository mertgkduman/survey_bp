# BB72 CSS BP study v1 evidence

This directory contains the frozen, verified controlled CSS study on the source-pinned [[72,12,6]] BB72 code. Open `study.html` for the offline interactive view and `REPORT.md` for the statistical readout. The original paper's circuit-level BP-OSD experiment is not reproduced here. The BP-SF arm uses canonical SPA messages and deterministic test order, unlike the source paper's min-sum and parallel selection.

Each arm's uncompressed ledger remains on the HPC filesystem. GitHub stores a deterministic `events.jsonl.gz` beside the arm's manifest and result. To restore one ledger, run `gzip -dc events.jsonl.gz > events.jsonl`; its SHA-256 must equal that arm's `raw_sha256` in `publication-manifest.json` and `ledger_sha256` in its `result.json`.

`selection-lock.json` binds the independently sampled parameter-selection cohort. `result.json` binds the evaluation arm ledgers and their matched sample identities. Operational Slurm logs are local-only and are not outcome evidence.
