# PriorTilt Table 4 — XYZ joint detector model

User-authorized reproduction of the released BB144 [[144,12,12]] XYZ comparison
at p=.003, using **50 CPUs per decoder/code/rate point**, shared across its
X- and Z-memory runs. Two points: PriorTilt and RelayBP-5. This is separate from
the preserved standard-XZ Fig.1 campaign. No beam XYZ source measurement or
additional error-rate grid is invented.

Source: https://arxiv.org/html/2611.13373v1, Table4; author repository
https://github.com/ionq-publications/PriorTiltDecoder at
8eefd37d694b5942fe60ec6d5c82ce97f3d2a450. Exact XYZ circuits, full-precision
three-phase parameters, raw source counts and source license are retained.
Each memory DEM includes both detector types jointly:1728 detectors,67824/67752
fault mechanisms and391464/391320 edges for X/Z memories. Original error
instructions are retained one-to-one; no graphlike splitting, detector-sector
projection or dense check-matrix construction is used. Detector-column merge
collisions are absent. Physical noise remains the released circuit model.

PriorTilt:60 initial sweeps,6000 rounds of6, boundaries50/420 and source phases.
RelayBP-5:80 initial sweeps,600 additional legs of60, gamma0=.125 and uniform
[-.24,.66) fields; stop at5 converged legs, counting duplicate candidates.
Select the first strict minimum of sum(original prior LLRs on candidate support).
Retain the first-leg candidate if every leg fails. Source paper specifies601
TOTAL legs and36080 sweeps; raw CSV labels that total num_sets601, whereas native
Rust's num_sets counts ADDITIONAL legs. Native comparison therefore passes600.
This interpretation and unchanged raw CSV are explicitly recorded in source.json.

Both controllers use the unchanged canonical float64 min-sum sweep, alpha1,
o offset/cap and source hard ties. The new relay-list policy is versioned
separately; frozen first-solution Relay/Beam/PriorTilt execution is unchanged.
Canonical total-minus extrinsic arithmetic and indexed policy RNG differ from
native prefix/suffix reductions and RNG; this is a qualified canonical adaptation.
All converged Relay candidates' scores, hashes, strict-improvement flags and leg
work are retained in the8-column trace. No decoder receives hidden truth.

Metric=(X-memory observable failure probability+Z-memory observable failure
probability)/12, as released. Nonconvergence is independently recorded rather
than automatically counted as a logical error. Per-basis stop20 errors or100M
shots, exact ordered prefix;97.5% capped exact component intervals are summed
and divided by12 for pointwise at-least95% X/Z coverage. Authors' roughly100
errors per basis and1-sigma uncertainties remain separate. Raw source counts
are in source-data/ and reconstructed source-table4.csv.

Each point uses50 single-thread process workers on one Slurm node,96GiB,
four-day walltime/requeue, private job JIT cache and sealed shared Stim samples.
Batch size64 limits speculative work and checkpoint latency for the larger DEM;
full-budget separate-seed pilot timings are recorded in qualification.json.
Commit by global shot order per basis, sharing the pool between memories.
Retain all sealed speculative stages and report their extra work separately;
never include them in LER. Unsealed interrupted work is unmeasured. Resume
validates committed evidence and replays endpoints. Fresh-process final audits
reevaluate every original DEM candidate/logical equation, leg work and endpoints,
including all speculative stages, before a receipt can enter report.py.

Instrumented decoder time excludes sampling/evaluation/audit/I/O.50-process
cohorts are explicit; no single-core or paper-hardware latency equivalence is
claimed. Both mean iterations and directed edge updates are exported per basis.
Raw results remain under local ignored results/; plan/manifest/audit hashes bind
publication. Empty reports contain no provisional local rate. No public v2
catalog curve is created from a single physical error rate.

Workflow: qualify.py on50 CPUs -> run.py --freeze -> control.py submit.
Refresh only with report.py. Qualification is excluded from production seeds,
counts and results. plan.json binds all source, controller, test and launcher
bytes; resource-amendment.json binds the50-CPU resource contract. Frozen files
must not change while results are live.
