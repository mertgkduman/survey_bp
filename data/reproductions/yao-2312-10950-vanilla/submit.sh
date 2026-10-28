#!/usr/bin/env bash
# Submit the frozen 128-shard campaign on Duke's common partition.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STUDY_ROOT="$REPO_ROOT/data/reproductions/yao-2312-10950-vanilla"
mkdir -p "$STUDY_ROOT/results/logs"
COUNT="$(python - "$STUDY_ROOT/campaign.json" <<'PY'
import json,sys
print(len(json.load(open(sys.argv[1]))['tasks']))
PY
)"
sbatch --parsable --account=pfisterlab --partition=common \
  --job-name=yao-vanilla --cpus-per-task=1 --mem=4G --time=06:00:00 \
  --array="0-$((COUNT-1))%12" \
  --output="$STUDY_ROOT/results/logs/%A_%a.out" \
  --error="$STUDY_ROOT/results/logs/%A_%a.err" \
  --chdir="$REPO_ROOT" \
  --export=ALL,OMP_NUM_THREADS=1,PYTHONPATH=src \
  --wrap="python data/reproductions/yao-2312-10950-vanilla/run_task.py"
