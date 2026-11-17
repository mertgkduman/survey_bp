# OSD v2 qualification evidence

The **final qualified implementation and tables** are in
[qualified/QUALIFICATION.md](qualified/QUALIFICATION.md), with its sealed raw
measurements in [qualified/benchmark.json](qualified/benchmark.json).

Root `benchmark.json`, `RESULTS.md`, fixtures and ledgers retain the initial
implementation run (Slurm61981163). `initial-source/` retains its exact inputs.
The qualified run (Slurm61984549) reuses the same fixture bytes and compares the
initial implementation directly within each matched timing round. Both jobs
completed on one CPU. Slurm61986557 independently replayed every published
equivalence/pipeline event in a fresh process.

```sh
PYTHONPATH=src .venv/bin/python scripts/benchmark_osd_v2.py --verify
PYTHONPATH=src .venv/bin/python scripts/benchmark_osd_v2.py --verify --historical --output data/benchmarks/osd-v2
```

`scripts/report_osd_v2.py` derives the detailed tables without new timings.
`scripts/verify_osd_v2.py` performs full fresh replay; its receipt binds both
measurement and derived-report manifests. Use a new output location and source
pin for later measurements rather than replacing these sealed files.

Full API, score, enumeration, evidence and work contracts:
[docs/osd-v2.md](../../../docs/osd-v2.md).
