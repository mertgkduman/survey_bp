# Verified corrected p=0.05 pilot v2 evidence

This v2 run supersedes the invalidated v1 diagnostic run. The aggregate
`events.jsonl` is kept uncompressed on the HPC filesystem for
verification. GitHub stores `events.jsonl.gz` because the raw aggregate is too
large for an ordinary GitHub file. Restore it with:

```bash
gzip -dc events.jsonl.gz > events.jsonl
```

The restored file's SHA-256 must equal `ledger_sha256` in `result.json`.
Individual arm ledgers are stored uncompressed and can be inspected directly.
