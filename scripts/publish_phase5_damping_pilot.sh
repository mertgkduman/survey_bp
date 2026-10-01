#!/usr/bin/env bash
# Publish only the verified, sealed Phase 5 p=0.05 run artifacts.
set -euo pipefail

cd /hpc/group/pfisterlab/mg551/storage/survey_bp
base=data/results/phase5-interventions/b1-p005-damping-pilot

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

git add -- "$base/events.jsonl" "$base/result.json" "$base/summary.json" "$base/REPORT.md" \
    "$base"/*/manifest.json "$base"/*/events.jsonl "$base"/*/result.json
git diff --cached --check
git commit -m 'Publish verified matched p=0.05 intervention and damping pilot'
git push origin HEAD:main
git ls-remote origin refs/heads/main
