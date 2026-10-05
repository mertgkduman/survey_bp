#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
root="$PWD"
output=data/results/fair-beam-relay-css-v2
integration=/hpc/home/mg551/gsd-workspaces/integration-fair-beam-relay-main/survey_bp
python_bin=/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python
base=0479b44c13806325e0dbc9b08d733758a2d77fe0

[[ "$(git branch --show-current)" == feat/fair-beam-relay-campaign ]]
[[ -z "$(git status --porcelain --untracked-files=no)" ]]
"$python_bin" scripts/package_fair_beam_relay_campaign_v2.py package > "$output/package-job.json"
"$python_bin" scripts/package_fair_beam_relay_campaign_v2.py verify-package > /dev/null

"$python_bin" - <<'PY'
import json
from pathlib import Path
import subprocess

root = Path("data/results/fair-beam-relay-css-v2")
manifest = json.loads((root / "publication-manifest.json").read_text())
paths = [str(root / name) for name in sorted(manifest["files"])]
paths.append(str(root / "publication-manifest.json"))
subprocess.run(["git", "add", "--", *paths], check=True)
PY

git diff --cached --quiet && { echo 'Terminal campaign package already committed' >&2; exit 1; }
git commit -m 'Publish matched BB72 BeamSearch and RelayBP evaluation evidence'
git push origin HEAD:refs/heads/feat/fair-beam-relay-campaign

[[ -z "$(git -C "$integration" status --porcelain)" ]]
git -C "$integration" fetch origin main
[[ "$(git -C "$integration" rev-parse origin/main)" == "$base" ]]
[[ "$(git -C "$integration" rev-parse HEAD)" == "$base" ]]
git -C "$integration" merge --no-ff feat/fair-beam-relay-campaign -m 'Merge matched BB72 BeamSearch and RelayBP campaign'
"$python_bin" "$integration/scripts/package_fair_beam_relay_campaign_v2.py" verify-package > /dev/null
"$python_bin" -m pytest "$integration/tests/test_run_fair_beam_relay_campaign.py" -q
git -C "$integration" push origin HEAD:refs/heads/main
printf 'Published main commit %s\n' "$(git -C "$integration" rev-parse HEAD)"
