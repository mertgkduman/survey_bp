# XYZ reproduction qualified and launched

Scope is the authors' Table 4 comparison: BB144 [[144,12,12]], physical circuit
error rate p=.003, 12 syndrome cycles. Two paired-memory decoder points,
PriorTilt and RelayBP-5, each sharing 50 process workers between its X- and
Z-memory experiments. Both production points are RUNNING with 50 allocated
Slurm CPUs, 96GiB and four-day requeueable allocations: **62102101_0** and
**62102101_1**. The dependent collector is **62102102** (requested one reporting
CPU; Slurm allocates two for its 12GiB memory request). Simulation allocation
is 100 CPUs total. All 100 production decoder processes initialized and match
the exact expected source-model execution hashes.

This is full joint XYZ detector decoding, preserving each original DEM fault
mechanism. Both detector types enter each memory graph. X/Z memory graphs have
1728 checks, 67824/67752 fault variables and 391464/391320 edges respectively.
Independent author sparse H, A and probability vectors match exactly, with no
detector-column collisions. There is no dense H construction or detector-sector
split. Separate memory experiments determine which logical observables are
measured, while decoding uses their complete joint detector model.

PriorTilt uses the exact XYZ three-phase schedule, boundaries50/420,
60+6000x6=36060 maximum sweeps, and first-convergence return. RelayBP-5 uses
80+600x60=36080 maximum sweeps, source gammas and five converged legs, including
duplicates. Select the first strict minimum of original-prior LLR support score;
if all legs fail, return the initial failed candidate. The source CSV labels
601 total legs as num_sets601, whereas native Rust num_sets means additional
legs. We explicitly follow the paper's 601-total-leg cap and pass600 to native
qualification. Raw source CSV is unchanged.

The released source counts yield LER/cycle 1.0393921324477514e-5 for PriorTilt
and1.0956976636968136e-5 for RelayBP-5. No local statistical agreement is claimed
before production and full audits complete. Standing local stopping is20
observable errors or100M decoded shots per memory basis, with exact ordered
prefixes. Metric=(X-memory observable rate+Z-memory observable rate)/12;
nonconvergence remains separate. Local capped component intervals provide
pointwise at-least95% simultaneous X/Z coverage; author precision and1-sigma
bars are separate. No qualification outcomes or incomplete local rates enter
RESULTS.md/comparison.csv. Empty publication handling is tested and currently0/2.

## Qualification and preservation

95 affected regression cases pass, including existing PriorTilt/Relay/Beam/XZ
campaign tests. New checks include an independent weighted candidate/winner
oracle, exact-tie retention, duplicate counting, cap exhaustion/fallback,
returned-winner hash/score validation, exact parallel-prefix and resume behavior,
manifest tampering, empty/unaudited reporting, and enforcement of50-worker/Slurm
resource requirements. Historical canonical sweep and frozen first-solution
controllers are byte-unchanged; the new relay-list policy is separately versioned.

Successful qualification62100693 ran on50 CPUs.24 native Relay cases match
candidate, convergence, all-leg iterations and selected posterior using identical
explicit gamma fields and aligned native LLR initialization.128 actual XYZ
pilot events (32 shots per memory basis per method), with the full paper budgets,
pass full independent original-DEM candidate/logical evaluation, exact all-shot
serial replay of candidates/counters/traces and unchanged resume receipts.
Each method uses four fresh50-worker sampling/audit/resume pools:200 initialized
process receipts.15 PriorTilt and45 Relay process IDs sealed the short pilot
shot work; the allocation and initialized pools were50, without claiming50
distinct sealed-shot producers in these short pilots. Production independently
verifies all50 decoder process initializations per point.

Initial qualification62100295 failed before simulation because the native
references existed only in the login node's /tmp. The fix stages the identical
preexisting pinned native builds, source Python helpers and licenses in a
checksum-pinned shared reference archive. Both binary digests equal the prior
qualified builds. The failed log/accounting remain retained. Successful full
qualification precedes all production submission. Native arithmetic/RNG remain
separate from canonical float64 total-minus reductions and indexed randomness;
this is a canonical adaptation, not bitwise native replication.

Production uses64-shot sealed stages, ordered per-basis commits, exact trimming
at the global stopping event, and separate computed/retained/speculative work.
Final fresh-process audits cover all committed and sealed speculative candidates,
original H/A equations, work/selection traces and endpoint replay before any
point is publishable. Both mean all-path iterations and directed edge updates
are exported. Instrumented50-process latency excludes sampling/evaluation/audit/
I/O and is not compared as a matched single-core/paper-hardware benchmark.
Unsealed interrupted work is explicitly unmeasured.

Frozen plan d97473d7070bcc8bb9b904fbfc7d51645e6c2f5ae1f416a06cb876c4c9ea60c1;
resource amendment4bb2774e374cbf09a1e19144e54e6b5e23ae21b6ca2ea1482c5f94386fc261c5.
85 implementation/source/test files are bound, including all63 unchanged parent
frozen files. Implementation029786ac and qualified freeze3058dfd4 precede
production dispatch. Raw ledgers remain locally under ignored results/.

The original XZ campaign was neither cancelled nor rerun. Its final audit has
completed (39/39); its previously scheduled collector61971020 is independently
refreshing the large publication. Other collectors' pre-existing tracked outputs
remain outside staging. No public HTML/catalog/v1, old kernel, old frozen plan,
model selection or phase scientific gates were changed. XYZ is one physical
rate, so no singleton curve is injected into the public multi-rate catalog.
