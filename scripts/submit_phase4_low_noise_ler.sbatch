#!/bin/bash
#SBATCH --job-name=phase4-ler-bb144
#SBATCH --partition=common
#SBATCH --account=pfisterlab
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=7-00:00:00
#SBATCH --output=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1/slurm-%j.out
#SBATCH --error=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1/slurm-%j.err

set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONNOUSERSITE=1
export PYTHONPATH=/hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925/src
cd /hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925
exec /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python scripts/run_phase4_low_noise_ler.py \
  --run \
  --design data/evidence/phase4-low-noise-ler-design-v1.json \
  --output /hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/low-noise-ler-v1
