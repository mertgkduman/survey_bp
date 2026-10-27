#!/usr/bin/env bash
#SBATCH --job-name=bp4-ms-b1-p014-shards
#SBATCH --account=pfisterlab
#SBATCH --partition=common
#SBATCH --array=0-4%5
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=0-04:00:00
#SBATCH --output=from_dr_pfister_presentetations/results/ms_both_changes_curve/logs/%A_%a.out
#SBATCH --error=from_dr_pfister_presentetations/results/ms_both_changes_curve/logs/%A_%a.err

set -euo pipefail
cd /hpc/group/pfisterlab/mg551/storage/survey_bp
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1

index="${SLURM_ARRAY_TASK_ID}"
start=$((index * 2000))
output="from_dr_pfister_presentetations/results/ms_both_changes_curve/shards/b1_p0140_shard${index}"
exec .venv/bin/python -u from_dr_pfister_presentetations/run_ms_both_changes_curve.py \
  --code b1 --p 0.14 --shots 2000 --start-shot "$start" --seed 20261215 \
  --output "$output"
