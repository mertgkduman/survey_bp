#!/bin/bash
#SBATCH --job-name=phase4-ler-reconcile
#SBATCH --partition=common
#SBATCH --account=pfisterlab
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=7-00:00:00
#SBATCH --output=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1-accelerated/slurm-%j.out
#SBATCH --error=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1-accelerated/slurm-%j.err

set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONNOUSERSITE=1
export PYTHONPATH=/hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925/src
cd /hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925
exec /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python scripts/reconcile_phase4_low_noise_ler_parallel.py \
  --serial-root /hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1 \
  --parallel-root /hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-p0050-parallel-v1 \
  --output /hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1-accelerated \
  --serial-job-id "$SERIAL_JOB_ID" \
  --parallel-job-id "$PARALLEL_JOB_ID"
