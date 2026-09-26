# Phase 5 design tasks and implementation handoff

Date: 26 September 2026. These are bounded preparatory tasks, not numbered
execution plans. All six Phase 5 requirement IDs remain pending.

## Completed design work in this update

- Reviewed Phase 4 dependencies and gaps against code/evidence.
- Defined intervention, working-view, session, lift and restart contracts.
- Recorded two BPGD source ambiguities and impulse realization boundaries.
- Established deterministic shortening and original-validation fixtures.
- Defined state rollback, work categories, selection and timing boundaries.

## Next task map

| Task | Responsibility and proposed files | Requirement | Dependencies |
| --- | --- | --- | --- |
| D1 | Source decisions and availability records; data/evidence/phase5-source-decisions.json | MOD-02, MOD-03, INT-02, INT-03 | Primary-source discovery; can proceed now |
| D2 | Versioned working problem, fixation and lift contracts; canonical/problems.py, future transformations.py | INT-01, INT-02, MOD-03 | D1 operator definitions; Phase 4 gate for execution |
| D3 | Vector priors and BP round/session transition; canonical/kernel.py, future intervention_session.py | MOD-02, INT-03, INT-04 | D2 and corrected memory-state ownership |
| D4 | Source-qualified BPGD controller; future guided_decimation.py | MOD-02 | D1, D3; explicit zero/final-round decisions |
| D5 | Impulse attempt orchestration, lift and stable selection; future impulse.py | MOD-03 | D1, D2, D3 |
| D6 | Freezing, source-qualified flips and restarts; future interventions.py | INT-01, INT-02, INT-03, INT-04 | D1, D2, D3 |
| D7 | Public schema/ledger verifier, matched CSS fixtures and guide | All six | D4–D6; admitted finite pilot design |

## Acceptance checks to carry into execution plans

**D1:** Resolve paper versions/equations and zero/tie/final-round/numerical
rules. Distinguish finite-bias BPGD from exact constraints. Find and pin native
code, or retain an explicit unavailable/unverified status. Do not infer no
implementation exists from a failed search. Source-defined syndrome/sign
flips remain open until their primary algorithms are selected.

**D2:** Preserve originals; demonstrate shortening equivalence, map bijection,
all-fixed success/contradiction, dependent/empty checks and bad lift rejection.
Exercise a working-valid/original-invalid candidate. The standalone finite
algebra validator supplied now becomes an independent fixture oracle.

**D3:** Verify retained versus reset messages/histories, changed prior fields,
graph/cache invalidation and private RNG cursor. Denied units leave all parent
state unchanged; failures retain last committed diagnostics. The public
memory dispatch correction must be incorporated before memory is composed.

**D4:** On constructed graphs, check selected reliability, deterministic ties,
finite prior update, exclusion of decimated indices, T-unit round boundary,
declared zero rule, last-round behavior and original stopping. Reject hidden
truth in trigger and selection views. Preserve adapted variants as such.

**D5:** Check baseline-only success, failure trigger, independent attempts,
fixed-one contradiction, actual attempt caps, lifting, minimum original
weight, stable first-index alternative and worker-arrival invariance. Compare
an eligible pinned native implementation only when available.

**D6:** Check fixation lifetime/release, syndrome certificate or original
rejection, sign target/value and cache consequences, independent restart
streams and reset/preservation compatibility. Count work from failed and
denied paths honestly, without fabricating completed operations.

**D7:** Public manifests reject unsupported combinations; malformed/rehashed
semantic changes fail verification. Enable/disable interventions on matched
CSS development samples under finite caps, expose five outcome cells and
candidate origins, and execute a bounded guide. Pilot labels remain
adaptation/not_assessed; no curve agreement follows from fixture success.

## Source and measurement decisions still open

- Confirm native BPGD message continuation and resolve Algorithm 1 versus
  Equation 36 at zero, plus the final round boundary.
- Pin impulse code and its infinite-prior convention; establish whether
  structural shortening is a source-equivalent realization or adaptation.
- Resolve exact syndrome/sign-flip algorithms; generic contracts are not
  enough to satisfy a source-defined requirement.
- Choose public schema/ledger versions and a typed compatibility matrix.
- Freeze pilot tolerances, attempt/work budgets and runtime protocol before
  sampling. Completed Phase 4 low-noise outcomes cannot choose these settings.

## Dependency decision

Design does not require calibration to have a winner. Formal Phase 5 execution
depends on the completed Phase 4 capability and evidence gates. The immediate
coding continuation is the isolated Phase 4 ablation/trace work described in
its handoff; D1 and interface design can advance alongside it.
