#!/usr/bin/env bash
#SBATCH --job-name=pfister-v2-curve
#SBATCH --account=pfisterlab
#SBATCH --partition=common
#SBATCH --array=0-11%6
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=2-00:00:00
#SBATCH --output=from_dr_pfister_presentetations/results/full_v2_curves/logs/%A_%a.out
#SBATCH --error=from_dr_pfister_presentetations/results/full_v2_curves/logs/%A_%a.err

set -euo pipefail
cd /hpc/group/pfisterlab/mg551/storage/survey_bp
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1

codes=(b1 b1 b1 b1 b1 b1 double_gross double_gross double_gross double_gross double_gross double_gross)
probs=(0.06 0.065 0.08 0.10 0.12 0.14 0.04 0.05 0.06 0.08 0.10 0.12)
labels=(0060 0065 0080 0100 0120 0140 0040 0050 0060 0080 0100 0120)
index="${SLURM_ARRAY_TASK_ID}"
code="${codes[index]}"
prob="${probs[index]}"
label="${labels[index]}"
seed=$((20261210 + index))
out="from_dr_pfister_presentetations/results/full_v2_curves/${code}_p${label}"
exec .venv/bin/python -u from_dr_pfister_presentetations/run_full_v2_curve.py \
  --code "$code" --p "$prob" --seed "$seed" --target-failures 30 \
  --max-shots 10000000 --max-iterations 1000 --output "$out"
