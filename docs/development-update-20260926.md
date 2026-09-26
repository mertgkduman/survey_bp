# Development and computational evidence update

Policy-Based BP Research Platform for QLDPC Decoding

26 September 2026. Evidence snapshot: 22:47 UTC. Active work: Phase 4,
Plan 12. This report includes completed implementation work, pending
simulations and preparatory Phase 5 design, with those statuses explicit.

## 1. What changed since the previous PDFs

The latest dated PDF is `docs/research-novelty-and-depth-register.pdf`,
recorded on 24 September in commit 2a83502. It added a prospective quaternary
memory research question. The latest broad technical PDF,
`docs/policy-bp-documentation-through-phase-2.pdf`, was recorded on 23 September
in 30df961 and ended at Phase 2. This update bridges that broader snapshot
with a short Phase 3 account and then documents the Phase 4 developments
since the novelty PDF. Both historical PDFs retain their exact bytes.

The main changes are a verified update/scheduling engine, active-memory
Relay execution and native-reference diagnostics, bounded calibration and
lower-noise estimation, a discovered ordinary-memory dispatch bug and its
isolated correction, guarded fresh-evaluation tooling, and an explicit design
for the next intervention phase.

The repository snapshot used here is main commit af09c5e. The memory correction
is commit fc214ef in a separate worktree; it has not been merged into the
active simulation source. Frozen data, source paths, original design bytes,
historical PDF hashes and capture time are retained in
`docs/evidence/development-snapshot-20260926.json`.

## 2. Phase 3: update rules and scheduling

Phase 3 completed on 24 September with all 17 plan summaries and its
verification gate passed. It added min-sum, normalized min-sum and offset
min-sum conventions; layered, check-serial and variable-serial schedules;
residual priorities and cache semantics; randomized ordering with replayable
streams; and a source-qualified Hsu group schedule. These remain policies
inside the compatible canonical binary engine.

The phase verification recorded 300 passing tests. Retained policy pilots
contain 19 verified one-shot terminals, plus two Hsu terminals. Their value
is checking equations, ordering, compatibility, rollback and provenance.
Those tiny pilots are not statistical curve reproduction. Hsu's schedule is
a declared binary CSS adaptation of its classical problem. The separate
Moradi qualifier remains unavailable without the author partition and Q-table.

Authority: `.planning/phases/03-update-rules-and-scheduling/03-VERIFICATION.md`.
These are historical Phase 3 gate counts, not a new full-suite run for this PDF.

## 3. Three comparisons that must remain distinct

| Arm | Execution | Meaning |
| --- | --- | --- |
| Source-procedure | Canonical Python engine, min-sum | Declared realization of the source's BP procedure with CSS adaptation limits |
| Canonical-default | Canonical Python engine, sum-product | Same engine family, different update rule and possibly different stopping/work |
| Author-native | Separately staged author Rust decoder | Executable reference pinned to relay v0.2.2 |

The native author pin is
`14cb31a18f9b9d7d099791b793e35b8a2951f8f3`. Native environments remain
isolated from canonical execution. Source-procedure does not mean that the
GitHub Rust code ran; it means that the specified source behavior was expressed
in our canonical engine. Native evidence is named explicitly when that code
actually runs.

The controlled source-procedure versus canonical-default comparison changes
the BP update rule from min-sum to sum-product while preserving common declared
controls. Both run in Python. Their timing differences can include update
cost, convergence paths and amount of work. A separately tuned comparison
may additionally use different selected coefficients; it must disclose that.

Author-native versus canonical comparisons have a Rust/Python implementation
difference and can also differ in numerical conventions, trajectories,
instrumentation and timing scope. Recorded pipeline ratios cannot isolate
a language effect.

## 4. Memory and Relay development

Relay executes affine-prior memory dynamically at source-iteration boundaries,
with uniform first-leg and declared disordered later-leg parameters.
Sequential legs transfer the previous posterior; new leg messages and private
histories follow explicit reset rules. Source and canonical numerical profiles,
gamma identities, leg work and terminal reasons remain visible.

Artifact qualification resolved the B1 identity discrepancy instead of treating
matching code parameters as identical matrix evidence. The benchmark/caps
work now uses reconciled B1, BB-144 and generated HGP artifacts with their
different source-status qualifications. Bounded calibration selects settings
using retained outcomes and work under a frozen rule. Fresh evaluation has
its own sample namespace.

### Ordinary-memory execution correction

During continued coding, the public ordinary-memory V4 runner was found to
validate memory bindings and then discard them in its compact V3 projection.
Such runs executed plain BP. The isolated correction uses full compact V5
dispatch and executes affine-prior, V2C damping, PDBP, PD-prime and momentum
memory at whole flooding-sweep boundaries.

The correction adds private per-binding histories, atomic budget/state
commit, explicit prior -> posterior/belief -> V2C operand ordering, history
digests and element-work accounting, and independent semantic reconstruction.
Momentum now exposes the required alpha/gamma parameters. PD-prime uses an
O(n) sufficient statistic with declared first-field/prior assumptions.

Failed budget/iteration-limited runs retain the last committed diagnostic
candidate and its origin; it remains unselected when invalid. Rehashed
semantic tampering is rejected. Numerical failure and denied work preserve
the appropriate committed prefix and private histories.

The correction handoff records a regression run of **356 passed, one existing
skip**, then a final focused memory/manifest gate of **67 passed**. These are
implementation fixtures on fc214ef, not newly simulated campaign shots.
The existing skip concerns the unfinished Phase 4 notebook identity workflow.

The live Relay campaign uses a separate dispatch and was unaffected by this
ordinary-memory bug. Historical ordinary-memory results retain their original
plain-BP meaning. Additional local schedules, history lifetimes, retained
histories, ordinary disordered assignment and per-iteration NMS still need
execution support; fixture success does not close those gaps.

## 5. Computational evidence available now

### Completed lower-noise estimation

This is the BB-144 independent X-only CSS code-capacity experiment, with four
arms receiving the same identified physical samples at each rate and shot.
It uses fixed, uncalibrated settings: first gamma 0.125, later center 0.25,
width 1.25, an 80-iteration first leg, 60-iteration later legs, up to 31 Relay
legs and one solution. Baseline arms have one leg. The numerical profiles
are float64 SPA or min-sum as named in Section 3.

| Physical error rate | Arm | Shots | All-shot failures | Failure LER | Exact interval, percent |
| --- | --- | --- | --- | --- | --- |
| 0.05 | SPA baseline | 8192 | 337 | 4.114% | 3.512–4.782 |
| 0.05 | SPA Relay | 8192 | 289 | 3.528% | 2.971–4.152 |
| 0.05 | Min-sum baseline | 8192 | 353 | 4.309% | 3.693–4.991 |
| 0.05 | Min-sum Relay | 8192 | 290 | 3.540% | 2.982–4.165 |
| 0.06 | SPA baseline | 2048 | 198 | 9.668% | 7.889–11.679 |
| 0.06 | SPA Relay | 2048 | 178 | 8.691% | 7.002–10.619 |
| 0.06 | Min-sum baseline | 2048 | 219 | 10.693% | 8.826–12.787 |
| 0.06 | Min-sum Relay | 2048 | 186 | 9.082% | 7.356–11.044 |

The retained design prespecified six looks: 256, 512, 1024, 2048, 4096 and
8192 shots; at least 50 failures and relative interval half-width at most 0.35
for both all-shot failure and valid-selected conditional logical error in
all four arms at a rate. Its two-sided Clopper–Pearson intervals spend alpha
across looks and the two precision metrics at each arm/rate. Cell intervals
have their separate correction. The table uses the stored primary intervals;
it does not claim simultaneous coverage across every arm and rate.

The p=0.06 cohort reached these precision criteria at 2048 shots per arm;
p=0.05 reached them at 8192. Reconciliation finished at 19:07 UTC on
26 September with status `completed_precision`. There was no prespecified
cross-arm difference/ranking test. Smaller point estimates do not establish
statistically significant improvement. This is an uncalibrated controlled
CSS adaptation, not source-curve reproduction or a universal decoder ranking.

Result authority:
`data/results/phase4-memory-relay/low-noise-ler-reconciled-20260926/result.json`.
The original design lives in the separate low-noise worktree at c94064e;
a hash-verified byte-identical copy is packaged as
`docs/evidence/phase4-low-noise-design-snapshot-20260926.json`.

### Outcome categories and denominators

The reported diagnostic proposal categories are:

- **Valid-correct:** original syndrome matches and logical action agrees.
- **Valid-wrong logical:** syndrome matches but logical action disagrees.
- **Invalid-correct projection:** syndrome fails while the projection onto the
  pinned logical basis agrees. This is not a valid recovery.
- **Invalid-wrong projection:** syndrome fails and that projection disagrees.
- **No proposal:** no retained diagnostic bit vector exists to classify.

Invalid candidates are not assigned code-space logical cosets. Their logical
projection is a separate, basis-dependent diagnostic. A diagnostic proposal
and a selected recovery are also different objects: BP can propose a bit
vector that selection rejects because its syndrome is invalid. That is not
the same as producing no vector.

At p=0.05 the five cells are:

| Arm | Valid-correct | Valid-wrong | Invalid-correct | Invalid-wrong | No proposal |
| --- | --- | --- | --- | --- | --- |
| SPA baseline | 7855 | 155 | 0 | 182 | 0 |
| SPA Relay | 7903 | 289 | 0 | 0 | 0 |
| Min-sum baseline | 7839 | 118 | 2 | 233 | 0 |
| Min-sum Relay | 7902 | 290 | 0 | 0 | 0 |

All rows sum to 8192. All-shot failure counts every shot lacking a selected,
syndrome-valid, logically correct recovery, including no recovery/no proposal.
Conditional logical error uses only selected syndrome-valid recoveries. For
example, min-sum baseline has 353/8192 all-shot failures but 118/7957 conditional
logical errors. Its 235 invalid diagnostic proposals are not zero-error
recoveries. Both denominators and all cells must remain visible.

### Native-author diagnostics are present

A completed controlled diagnostic has 128 matched canonical/native pairs for
each of the three eligible codes. Native failures/timeouts were zero in these
retained pairs. The source pin and environment origin are recorded; a separate
bounded author test timed out and remains inconclusive rather than passing.

| Code | Matched pairs | Success disagreements | Exact candidate disagreements |
| --- | --- | --- | --- |
| Reconciled B1 | 128 | 10 | 37 |
| BB-144 | 128 | 3 | 16 |
| Generated HGP | 128 | 9 | 65 |

Different bit vectors can still be valid equivalent recoveries. Conversely,
similar aggregate success rates do not establish identical procedures.
The retained diagnostics quantify disagreement and preserve uncertainty;
128 pairs are not an equivalence verdict or a source circuit-curve reproduction.
The result is in `author-v022-agreement-v1/result.json`, frozen in the snapshot.

### Calibration remains pending

At 22:47 UTC the calibration process was active after approximately 25 h 48 m.
Its serialized result retained 1750 attempt records: 672 in each B1 preset
and 406 in the BB-144 source-procedure preset. The plan contains 182 cells;
the result had 55 configuration records, including an unfinished cell.
These are snapshot counts, not a finalized completion percentage. The
evaluation namespace had not been accessed and no terminal selection was
claimed.

The long duration reflects multiple parameter configurations, matched shots,
possibly many BP/Relay units per shot and mandatory verification. The Python
implementation and process/setup boundaries also contribute. Trying several
gammas is one source of work; the recorded evidence does not isolate it as
the sole runtime cause. Increasing workers helped the separate lower-noise
campaign preserve its design while running four arms concurrently.

## 6. Runtime evidence and the next measurement

The completed native comparison already contains pipeline timings for matched
observations. Its median per-pair canonical/native ratios are:

| Code | Median recorded ratio | Canonical mean, seconds | Native mean, seconds |
| --- | --- | --- | --- |
| Reconciled B1 | 1.804 | 64.733 | 36.894 |
| BB-144 | 1.661 | 6.243 | 2.464 |
| Generated HGP | 2.065 | 5.594 | 2.751 |

The canonical timer covers the public CLI run plus mandatory verification.
The native timer covers observation preparation, gamma reconstruction,
the isolated author process/decoder and diagnostic classification. Calls
were canonical-first. Thus the native recorded pipeline was faster on these
samples, but these unequal boundaries do not give decoder-only speed or
the cost attributable to language.

The guarded fresh-evaluation runner in 43dafb5 includes separately timed
native decode calls and separate preparation/verification facts. An
equal-boundary comparison still needs canonical decoder-only calls timed
at the same input/output boundary with matched algorithm, controls,
numerical profile, stopping and thread/resource settings. Counterbalance
call order, disclose warmup, and report candidate outcomes and work alongside
latency. Missing native internal counters remain missing, not zero.

Authority: `author-v022-agreement-v1/runtime-comparison.json`; the snapshot
preserves its exact scope declarations and summary digest.

## 7. Plan review and forward design delivered here

The review identifies the unfinished calibration/evaluation/notebook gates,
the ordinary-memory integration prerequisite, factorial ordering discrepancy,
shared-view admission requirement and missing trace support. Plan 04-14's
coverage table describes intended coverage, not completed evidence. Details
are in the plan-review appendix.

Phase 5 now has proposed contracts for interventions, transformed working
problems, fixation, BP continuation, certified lifts, original validation,
restart streams, atomic commit, lineage and separate work categories. Its
next-task map covers MOD-02, MOD-03 and INT-01–04. Primary-source ambiguities,
native availability and unresolved flip variants remain explicit.

The structural shortening proposal has an executable independent algebra
check: **16,384 exhaustive finite cases passed**, together with four constructed
cases covering a misleading working syndrome, a certified lift, all-fixed
success/contradiction and finite-prior behavior. The retained fixture report
is `docs/evidence/intervention-design-validation-20260926.json`. These checks
validate a design equation, not a new decoder implementation or LER claim.

The key extension is that current `WorkingProblem` accepts only identity
graphs/syndromes. Interventions need a versioned working-view and lift API;
candidate validation must always reach the immutable original equation.
The new task map makes that dependency concrete before BPGD or impulse coding.

## 8. Next execution sequence

1. Continue the isolated Phase 4 ablation/trace implementation while the live
   calibration retains its source identity.
2. Preserve original factorial design/caps and freeze an outcome-independent
   execution supplement for coefficients and operand order before sampling.
3. Reconcile terminal calibration, freeze selections and admit any extra views
   explicitly; execute fresh matched evaluation and native reference pairs.
4. Complete ablations, bounded traces, the executable notebook and Phase 4
   verification gates, then integrate the isolated correction safely.
5. Convert the Phase 5 design into checked execution plans after Phase 4.
   Source discovery and interface design can continue meanwhile.

Beam/search remains Phase 6, optional fallback Phase 7, campaign qualification
Phases 8–9, correlated quaternary Phases 10–11, circuit decoding Phases 12–13
and publication Phase 14. All three regimes remain in the journal scope.

## 9. Rebuilding and interpreting this report

Run `.venv/bin/python tools/build_development_pdf.py` to rebuild this dated PDF,
or add `--check` to compare exact generated bytes. Its fixed Markdown
inventory includes this narrative, the plan review, Phase 5 design and task
map; a source manifest prints their hashes plus the retained evidence hashes.
PDF generation reads the frozen documentation snapshot rather than live
simulation progress, so later results cannot silently alter this report.

Read the detailed design's primary-source links for mathematical definitions.
Repository verifiers and retained ledgers remain the evidence authority.
Source interpretations and proposed contracts are explicitly separated from
implemented behavior and computational measurements.
