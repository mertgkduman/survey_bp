# Observed Phase 1 development environment

Observed on 2026-09-22 UTC on `dcc-core-ferc-u-ac39-4-1.rc.duke.edu`.
These are local observations, not publication pins or a portability guarantee.
Repeat the probe on each execution node before interpreting a run.

| Item | Observed value |
|---|---|
| Python | 3.12.2, Anaconda build, GCC 11.2.0 |
| Executable | `/hpc/home/mg551/miniconda3/bin/python` |
| Platform | Linux 5.14.0-687.29.1.el9_8.x86_64, glibc 2.34 |
| NumPy | 2.2.6, `/hpc/home/mg551/miniconda3/lib/python3.12/site-packages` |
| SciPy | 1.17.1, same site-packages path |
| ldpc | 2.4.1, same site-packages path |
| pytest | 9.0.3, same site-packages path |
| pydantic | absent |
| bposd | absent |

Distribution versions and paths were read with `importlib.metadata.distribution`.
No package was installed during this probe. `conda` emitted a
`conda-libmamba-solver` entry-point warning; the active Python worked.

## Native API probe

With `OMP_NUM_THREADS=1`, `ldpc.BpDecoder` imported from
`/hpc/home/mg551/miniconda3/lib/python3.12/site-packages/ldpc/__init__.py`.
The constructor accepted `bp_method='product_sum'`, `schedule='parallel'`,
`input_vector_type='syndrome'`, `max_iter=10`, and `error_rate=0.1` for
`H = [[1,0],[0,1]]`. Decoding syndrome `[1,0]` returned candidate `[1,0]`,
`converge=True`, and `iter=1`. The C extension exposes no inspectable Python
constructor signature (`inspect.signature` raised `ValueError`).

The exact probe command was:

```bash
OMP_NUM_THREADS=1 python - <<'PY'
import numpy as np
from ldpc import BpDecoder
h = np.array([[1, 0], [0, 1]], dtype=np.uint8)
b = BpDecoder(h, bp_method='product_sum', schedule='parallel',
              input_vector_type='syndrome', max_iter=10, error_rate=0.1)
s = np.array([1, 0], dtype=np.uint8)
r = b.decode(s)
print(r.tolist(), bool(b.converge), int(b.iter))
PY
```

## Approved isolated development environment

On 2026-09-22, after the Plan 02 human package gate, `.venv` was created with
`python -m venv --system-site-packages .venv`. The user approved exact PyPI
versions `pydantic==2.13.5` and `bposd==2.1`; those were installed with
`.venv/bin/python -m pip install 'pydantic==2.13.5' 'bposd==2.1'`.
Their resolved dependencies were `pydantic-core==2.46.5`,
`annotated-types==0.8.0`, `typing-extensions==4.16.0`, and
`typing-inspection==0.4.4`. Existing NumPy, SciPy, ldpc, and pytest were
reused from the Anaconda site-packages directory and were not reinstalled.

`pydantic`, `pydantic-core`, and `bposd` import from
`/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/lib/python3.12/site-packages`;
NumPy, SciPy, ldpc, and pytest import from
`/hpc/home/mg551/miniconda3/lib/python3.12/site-packages`.
The full observed `pip freeze` is in `docs/environment-freeze.txt`.
Because this environment inherits system packages, reproduce it only on a
node with the same observed base package identities; a clean lock will be
needed before a portable release.
