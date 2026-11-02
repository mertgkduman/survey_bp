#!/bin/bash
#SBATCH --job-name=phase4-author-agreement
#SBATCH --partition=common
#SBATCH --account=pfisterlab
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=7-00:00:00
#SBATCH --output=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/author-v022-agreement-v1/slurm-%j.out
#SBATCH --error=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/author-v022-agreement-v1/slurm-%j.err

set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONNOUSERSITE=1
export PYTHONPATH=/hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925/src
cd /hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925
exec /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python scripts/run_phase4_author_v022_agreement.py \
  --run \
  --design data/evidence/phase4-author-v022-agreement-design-v1.json \
  --output /hpc/group/pfisterlab/mg551/storage/survey_bp/data/results/phase4-memory-relay/author-v022-agreement-v1
