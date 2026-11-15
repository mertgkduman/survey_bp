# Complete audit and tuning evidence

The completed study contains218 point workers,1,464 fresh confirmation measurements and163,668 separate tuning measurements. The full uncompressed verification receipt is434MiB; it and the original tuning CSV remain unchanged on the HPC filesystem. GitHub carries lossless gzip copies with byte-level round-trip checks and SHA-256 hashes in `evidence-archives.json`. Historical uncompressed snapshots remain in Git history.

To reconstruct the exact raw files before running the frozen analysis command:

```sh
gzip -dc verified.json.gz > verified.json
gzip -dc tuning-results.csv.gz > tuning-results.csv
```

The readable confirmation table is `iteration-results.csv`, and the formatted table is `RESULTS.md`. These retain every confirmed setting/cap, not only runtime-matched rows. Calibration and actual confirmation runtime ratios can differ; the independent completed-results assessment records this distinction.

No event ledger, raw receipt, manifest, simulation source or result value was removed or changed by compression. Raw event chunks remain in the local `results/` hierarchy. Catalog rebuilding uses the checked-in normalized extension and does not require decompression; the frozen collection/report scripts use the reconstructed raw files.
