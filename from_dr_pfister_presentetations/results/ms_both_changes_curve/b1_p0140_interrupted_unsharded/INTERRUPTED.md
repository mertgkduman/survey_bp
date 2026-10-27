# Interrupted unsharded B1 p=0.14 attempt

Slurm array task `60240869_4` was canceled on 2026-10-27 after about six
minutes because its projected runtime was much longer than the other points.
It had not emitted a completed shot block or summary; its zero-byte gzip
placeholder is retained as failed-run evidence. Five contiguous 2,000-shot
shards with the same seed and PCG64 stream replace this attempt. The planned
10,000-shot denominator is unchanged.
