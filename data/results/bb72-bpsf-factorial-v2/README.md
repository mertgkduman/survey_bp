# BB72 BP-SF factorial v2 evidence

This independent X-only CSS study compares SPA and min-sum updates, damping off/on, and BP-only 20/40-sweep controls against deterministic BP-SF. It does not reproduce the source's parallel execution or the Bravyi circuit-level BP-OSD experiment.

Open `study.html` for the offline interactive view and `REPORT.md` for the primary statistical assessment. `result.json` contains all 24 arm summaries, secondary descriptive contrasts, typed work, and runtime method/scope. Runtime is observed serial execution and is not a normalized source parallel-latency benchmark.

Each arm has a compressed `events.jsonl.gz` beside its manifest and result. Uncompressed ledgers and Slurm logs remain on the HPC filesystem. Restore a ledger with `gzip -dc events.jsonl.gz > events.jsonl` and compare its SHA-256 with `raw_sha256` in `publication-manifest.json`.
