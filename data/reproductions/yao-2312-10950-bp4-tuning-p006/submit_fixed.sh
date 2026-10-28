#!/usr/bin/env bash
# Submit a frozen refinement or validation plan from the repository root.
set -euo pipefail
stage="${1:?stage must be refine or validate}"
case "$stage" in refine|validate) ;; *) exit 2 ;; esac
root="data/reproductions/yao-2312-10950-bp4-tuning-p006"
plan="$root/${stage}_plan.json"
count=$(python -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["tasks"]))' "$plan")
mkdir -p "$root/results/logs"
sbatch --parsable --account=pfisterlab --partition=common \
  --job-name="yao-bp4-$stage" --array="0-$((count-1))%32" \
  --cpus-per-task=1 --mem=3G --time=03:00:00 \
  --output="$root/results/logs/%A_%a.out" \
  --error="$root/results/logs/%A_%a.err" \
  --wrap="OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_CACHE_DIR=/tmp/yao-bp4-${stage}-\${SLURM_ARRAY_TASK_ID} PYTHONPATH=src python $root/run_fixed_task.py --plan $plan"
