#!/usr/bin/env bash
# Submit the frozen, fixed-shot exploratory screen from the repository root.
set -euo pipefail
root="data/reproductions/yao-2312-10950-bp4-tuning-p006"
count=$(python -c 'import json; print(len(json.load(open("data/reproductions/yao-2312-10950-bp4-tuning-p006/screen_plan.json"))["tasks"]))')
mkdir -p "$root/results/logs"
sbatch --parsable --account=pfisterlab --partition=common \
  --job-name=yao-bp4-screen --array="0-$((count-1))%32" \
  --cpus-per-task=1 --mem=3G --time=02:00:00 \
  --output="$root/results/logs/%A_%a.out" \
  --error="$root/results/logs/%A_%a.err" \
  --wrap="OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python $root/run_task.py"
