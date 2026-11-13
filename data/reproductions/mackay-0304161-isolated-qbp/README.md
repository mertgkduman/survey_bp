# Undamped Q-BP and matched-channel binary controls

Both existing MacKay Construction-U codes, five depolarizing probabilities
.015/.0195/.030/.045/.060, SP float64-v2, d=0, no extra check cap, T=100.
Twenty terminal points compare joint Q-BP with separate X/Z binary BP on the
**same Pauli samples**, using confirmation seed2026111323 independently of the
1024-shot tuning seed. Q-BP receives the full depolarizing prior p; separate
binary decoders each receive the correct marginal prior 2p/3. All outcomes are
independently evaluated for syndrome validity and both logical residuals on the
original CSS code. No equations or canonical kernels are changed.

Each point stops at 20 quantum block failures or100,000,000 shots. One joint
iteration updates the full joint graph. One separate-BP paired round advances
both components, up to100 each, and its count is max(iter_X,iter_Z). Actual
component sweeps and both-directed-edge updates are retained separately; a
terminated component does not incur fictitious updates. Both graphs can spend
at most4*E*100 directed updates, where E is edges per component. The separate
implementation calls the existing binary kernel twice; independent component
stopping is equivalent to the noninteracting paired-round schedule.

The new d=0 Q-BP curve isolates damping relative to the existing d=.1/.95 joint
confirmation. The matched d=0 separate-BP comparison isolates joint versus
separate decoding under the same channel. Previous X-only binary BP remains a
distinct experiment. Shared samples across arms are never pooled as independent
observations. Source ordering/numerics and the inferred100 iteration budget
remain adaptations, not recovered historical specifications.

The user requested finishing these controls before moving on. Pending advance
61773603 was canceled; the last confirmation worker remains active. New final
advance requires all20 controls plus all40 old confirmation points, audits and
publishes them, and only then submits unchanged Roffe T=n. At most8 new one-CPU
workers run. Repeated dispatch is locked and reuses scheduler receipts.

The requested length74 paper ordinates are unavailable in arXiv versions1–3.
See paper-evidence.json and PAPER-EVIDENCE.md: the paper supplies a fixed-error
summary point, not a five-rate curve. All five requested values stay null.

Commands (PYTHONPATH=src and OMP/BLAS threads=1):

```
.venv/bin/python data/reproductions/mackay-0304161-isolated-qbp/run.py --freeze
.venv/bin/python data/reproductions/mackay-0304161-isolated-qbp/run.py --test-only
.venv/bin/python data/reproductions/mackay-0304161-isolated-qbp/run.py --submit
.venv/bin/python data/reproductions/mackay-0304161-isolated-qbp/run.py --collect
```

Collection audits retained evidence and starts no new samples. Preserve frozen
plans and do not submit the old canceled continuation separately.
