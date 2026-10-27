#!/usr/bin/env bash
#SBATCH --job-name=bp4-ms-both-curve
#SBATCH --account=pfisterlab
#SBATCH --partition=common
#SBATCH --array=0-8%6
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=0-12:00:00
#SBATCH --output=from_dr_pfister_presentetations/results/ms_both_changes_curve/logs/%A_%a.out
#SBATCH --error=from_dr_pfister_presentetations/results/ms_both_changes_curve/logs/%A_%a.err

set -euo pipefail
cd /hpc/group/pfisterlab/mg551/storage/survey_bp
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1

# Seeds reproduce each point's existing full-v2 PCG64 error stream.
codes=(b1 b1 b1 b1 b1 double_gross double_gross double_gross double_gross)
probs=(0.06 0.08 0.10 0.12 0.14 0.06 0.08 0.10 0.12)
labels=(0060 0080 0100 0120 0140 0060 0080 0100 0120)
seeds=(20261210 20261212 20261213 20261214 20261215 20261218 20261219 20261220 20261221)
index="${SLURM_ARRAY_TASK_ID}"
code="${codes[index]}"
prob="${probs[index]}"
label="${labels[index]}"
seed="${seeds[index]}"
output="from_dr_pfister_presentetations/results/ms_both_changes_curve/${code}_p${label}"
exec .venv/bin/python -u from_dr_pfister_presentetations/run_ms_both_changes_curve.py \
  --code "$code" --p "$prob" --shots 10000 --seed "$seed" --output "$output"
