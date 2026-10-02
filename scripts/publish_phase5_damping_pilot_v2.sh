#!/usr/bin/env bash
# Publish only the verified, corrected Phase 5 p=0.05 v2 run artifacts.
set -euo pipefail

cd /hpc/group/pfisterlab/mg551/storage/survey_bp
base=data/results/phase5-interventions/b1-p005-damping-pilot-v2

if [[ ! -f "$base/summary.json" || ! -f "$base/REPORT.md" ]]; then
    echo 'Refusing to publish without the verified v2 summary and report.' >&2
    exit 1
fi
python - <<'PY'
import json
from pathlib import Path
root = Path('data/results/phase5-interventions/b1-p005-damping-pilot-v2')
report = json.loads((root / 'summary.json').read_text())
assert report['verification']['status'] == 'passed'
assert report['verification']['shots'] == 128
assert report['verification']['arms'] == 14
PY

if [[ -n "$(git diff --cached --name-only)" ]]; then
    echo 'Refusing to publish while another change is staged.' >&2
    exit 1
fi
local_head=$(git rev-parse HEAD)
remote_head=$(git ls-remote origin refs/heads/main | cut -f1)
if [[ "$local_head" != "$remote_head" ]]; then
    echo "Refusing to publish: local HEAD $local_head differs from origin/main $remote_head." >&2
    exit 1
fi

gzip -n -9 -c "$base/events.jsonl" > "$base/events.jsonl.gz.tmp"
mv "$base/events.jsonl.gz.tmp" "$base/events.jsonl.gz"
cat > "$base/README.md" <<'EOF'
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
EOF
if [[ $(stat -c %s "$base/events.jsonl.gz") -ge 100000000 ]]; then
    echo 'Compressed aggregate exceeds the GitHub file size limit.' >&2
    exit 1
fi

git add -- "$base/events.jsonl.gz" "$base/README.md" "$base/result.json" "$base/summary.json" "$base/REPORT.md" \
    "$base"/*/manifest.json "$base"/*/events.jsonl "$base"/*/result.json
git diff --cached --check
git commit -m 'Publish verified corrected p=0.05 intervention and damping pilot v2'
git push origin HEAD:main
git ls-remote origin refs/heads/main
