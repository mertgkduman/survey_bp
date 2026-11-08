#!/bin/bash
#SBATCH --account=pfisterlab
#SBATCH --partition=gpu-common,scavenger-gpu,scavenger-h200
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=bp-gpu-qualify
set -euo pipefail
source /etc/profile.d/modules.sh
module load CUDA/12.8
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
.venv/bin/python -m pytest tests/canonical/test_gpu_flooding.py -q
.venv/bin/python .planning/quick/261108-meg-implement-compatible-circuit-policies-an/gpu-qualify.py .planning/quick/261108-meg-implement-compatible-circuit-policies-an/gpu-final
