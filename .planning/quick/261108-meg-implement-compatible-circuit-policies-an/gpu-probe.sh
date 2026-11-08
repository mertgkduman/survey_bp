#!/bin/bash
#SBATCH --account=pfisterlab
#SBATCH --partition=gpu-common
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:02:00
#SBATCH --job-name=bp-gpu-probe
set -euo pipefail
source /etc/profile.d/modules.sh
module load CUDA/12.8
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
.venv/bin/python - <<'PYCUDA'
from numba import cuda
from numba.cuda.cudadrv.libs import get_cudalib
import numpy as np
print('available',cuda.is_available(), 'NVVM',get_cudalib('nvvm'))
@cuda.jit
def add(x):
 i=cuda.grid(1)
 if i<len(x):x[i]+=1
x=cuda.to_device(np.arange(4,dtype=np.float64));add[1,32](x);print(x.copy_to_host())
PYCUDA
