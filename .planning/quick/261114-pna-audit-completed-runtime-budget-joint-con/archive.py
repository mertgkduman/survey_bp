"""Lossless public archives of large derived receipts; local raw bytes remain."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'


def digest(path, compressed=False):
    value = sha256()
    with (gzip.open(path, 'rb') if compressed else path.open('rb')) as stream:
        for chunk in iter(lambda: stream.read(2**20), b''): value.update(chunk)
    return value.hexdigest()


def main():
    records = []
    for name in ('verified.json', 'tuning-results.csv'):
        source = ROOT / name; destination = ROOT / (name+'.gz'); temporary = ROOT / (name+'.gz.tmp')
        raw_sha = sha256(); size = 0
        with source.open('rb') as incoming, temporary.open('wb') as output:
            with gzip.GzipFile(filename='', fileobj=output, mode='wb', compresslevel=6, mtime=0) as packed:
                for chunk in iter(lambda: incoming.read(2**20), b''):
                    raw_sha.update(chunk); size += len(chunk); packed.write(chunk)
        assert digest(temporary, compressed=True) == raw_sha.hexdigest()
        assert temporary.stat().st_size < 95*1024**2
        temporary.replace(destination)
        records.append({'raw_path': name, 'raw_bytes': size, 'raw_sha256': raw_sha.hexdigest(),
                        'archive_path': destination.name, 'archive_bytes': destination.stat().st_size,
                        'archive_sha256': digest(destination), 'lossless_roundtrip_checked': True})
        print(records[-1], flush=True)
    manifest = {'schema': 'lossless-research-receipt-archives-v1', 'study': 'roffe-joint-controls-runtime-budget',
                'plan_sha256': digest(ROOT / 'plan.json'), 'files': records,
                'note': 'Original raw files remain on the HPC filesystem unchanged. Reconstruct with gzip -dc archive.gz > raw_path. Frozen execution/report code continues to use raw paths.'}
    (ROOT / 'evidence-archives.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (ROOT / 'EVIDENCE.md').write_text('''# Complete audit and tuning evidence

The completed study contains218 point workers,1,464 fresh confirmation measurements and163,668 separate tuning measurements. The full uncompressed verification receipt is434MiB; it and the original tuning CSV remain unchanged on the HPC filesystem. GitHub carries lossless gzip copies with byte-level round-trip checks and SHA-256 hashes in `evidence-archives.json`. Historical uncompressed snapshots remain in Git history.

To reconstruct the exact raw files before running the frozen analysis command:

```sh
gzip -dc verified.json.gz > verified.json
gzip -dc tuning-results.csv.gz > tuning-results.csv
```

The readable confirmation table is `iteration-results.csv`, and the formatted table is `RESULTS.md`. These retain every confirmed setting/cap, not only runtime-matched rows. Calibration and actual confirmation runtime ratios can differ; the independent completed-results assessment records this distinction.

No event ledger, raw receipt, manifest, simulation source or result value was removed or changed by compression. Raw event chunks remain in the local `results/` hierarchy. Catalog rebuilding uses the checked-in normalized extension and does not require decompression; the frozen collection/report scripts use the reconstructed raw files.
''')
    extension = json.loads((ROOT / 'catalog.json').read_text())
    assets = [{'path': str((ROOT / name).relative_to(REPO)), 'kind': 'json' if name.endswith('.json.gz') else 'csv', 'label': label}
              for name, label in [('verified.json.gz', 'Complete audit receipt (gzip)'), ('tuning-results.csv.gz', 'All tested tuning settings/caps (gzip)')]]
    for dataset in extension['datasets']: dataset['assets'] = assets
    (ROOT / 'catalog.json').write_text(json.dumps(extension, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__': main()
