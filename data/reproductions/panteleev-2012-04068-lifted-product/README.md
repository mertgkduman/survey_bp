# Original lifted-product [[1054,140]] full decoder stack

User-selected source: Panteleev and Kalachev, *Quantum LDPC Codes with Almost Linear Minimum Distance*, arXiv:2012.04068v2, Example4. This is LP(A,A*) over circulants of size31, using the published3x5 exponent matrix. `source.py` constructs the exact checks; paired logical representatives are derived algebraically. The paper reports unsuccessful searches for logical words below weight20, not a certified distance20.

The original paper contains no LER curve, physical-rate grid or numeric decoding cap for1054. These measurements are **controlled canonical adaptations**, not a reproduction of nonexistent paper ordinates. The prospective depolarizing grid is p=0.02,0.04,0.06,0.08,0.10,0.12. The baseline min-sum scale0.625 and32-iteration ceiling come from Section3 of its cited BP-OSD paper, arXiv:1904.02703v3. That paper uses layered scheduling and nonbinary BP; this campaign uses our existing canonical flooding kernels. An iteration has a different schedule here. No claim of original native runtime, schedule identity or statistical paper agreement is made.

Twelve arms per rate: binary BP; correlated quaternary Q-BP; binary BP+OSD-0 and BP+OSD-CS-10; correlated Q-BP+OSD-0 and Q-BP+OSD-CS-10; tuned BP and tuned Q-BP; tuned RelayBP and beam search at32 and128 cumulative sweeps per CSS component. The128 budgets are explicitly4x exploratory search budgets, separate from the32 baseline. Every attempted branch, relay and both components contribute to work and latency. Q-BP+OSD derives binary posterior marginals from the joint I/X/Y/Z beliefs and uses detached OSD on each original component when joint BP fails. It is a canonical adaptation of the source's marginal postprocessing, not an assertion that the CS search matches the source's exhaustive OSD search.

All arms see the same indexed iid depolarizing Pauli stream within a stage/rate: I with1-p, X/Y/Z each p/3. Binary priors are2p/3, joint priors are the full Pauli distribution. The independent evaluator checks original syndromes and both logical residuals. Block failure means either component fails; derived word error rate is1-(1-LER)^(1/140). Invalid-syndrome failures remain in the denominator. No hidden truth reaches any decoder.

Numerical tuning uses damping0,.3,.5,.7; scale.5,.625,.8,1; offset0,.2, including the baseline. Search additionally varies segment length, unit count, beam width, solution count and relay memory range.32 numeric proposals per plain family and64 per search arm receive512 common training shots. The best four receive up to8192 independent finalist shots or40 failures. Minimum finalist block LER wins; exact ties prefer mean total sweeps, mean warmed runtime and configuration hash. Fresh confirmation uses an independent third seed and stops at20 logical failures or100,000,000 shots. All proposals and finalist results remain in separate ledgers/tables. Pointwise intervals use negative-binomial inversion at a failure stop and binomial inversion at the shot cap. No cross-point superiority claim follows from20 failures.

One single-threaded CPU is allocated to each arm/rate point, including tuning and both CSS components. JIT warm-up, sampling and independent evaluation are excluded from decoder latency. OSD work, marginal construction and all search paths are inside decoder timing. Report mean total sweeps, directed edge updates, OSD operations/candidate counts, mean latency and p50/p95/p99; quantiles use bounded-memory1%-wide bins.

Immutable64-shot gzip chunks provide exact restart, manifests pin every configuration/seed/stop/plan, and the plan pins code bytes, software and all imported kernels/controllers. A separate one-CPU audit per point checks every retained sample/candidate/outcome/work record, stopping, chunk hashes, training selection and canonical replay at both endpoints of every chunk. Dependent collection accepts only matching audit receipts. Active catalog curves group exact concrete settings and retain the central multi-rate eligibility rule; per-rate tuned settings are never merged to create an artificial curve. Raw ledgers remain local under ignored `results/`; compact source, dispatch, tables and audit receipts are versioned.

Run from the repository:

```
PYTHONPATH=src .venv/bin/python data/reproductions/panteleev-2012-04068-lifted-product/source.py
PYTHONPATH=src .venv/bin/python data/reproductions/panteleev-2012-04068-lifted-product/run.py --freeze
PYTHONPATH=src .venv/bin/python data/reproductions/panteleev-2012-04068-lifted-product/run.py --submit
PYTHONPATH=src .venv/bin/python data/reproductions/panteleev-2012-04068-lifted-product/run.py --collect
```

Sources: https://arxiv.org/abs/2012.04068v2 and https://arxiv.org/abs/1904.02703v3. Earlier BPGD, MacKay and Roffe evidence, frozen source files and canonical kernels are preserved.
