# Pitfalls Research

**Domain:** Policy-based BP-family QLDPC decoding research platform
**Researched:** 2026-09-21
**Confidence:** MEDIUM (primary papers and official project documentation checked; this is planning scoping, not a completed systematic review)

The source-backed observations below are distinguished from **proposed safeguards**, which are design recommendations for this project. Confidence refers to the evidence available for each pitfall, not to an empirical claim that the proposed platform already exhibits it. Phase names are topic names for the roadmap author to map to numbered phases. CSS code-capacity, correlated quaternary code-capacity, and circuit-level decoding all belong to the **first journal milestone**, in that order.

## Critical Pitfalls

### 1. Equating syndrome convergence with decoding success

**What goes wrong:** A candidate satisfying the measured syndrome is reported as a success even when its residual error acts as a nontrivial logical operator. Conversely, an estimate different from the sampled physical error is called a failure despite being stabilizer-equivalent. BPGD explicitly distinguishes syndrome failure, exact match, degenerate success, and logical failure. **Evidence: MEDIUM** ([BPGD, §2.3](https://arxiv.org/html/2312.10950v2)).

**Why it happens:** BP stopping checks a parity equation, while logical success checks the coset of the residual error. These are different predicates.

**How to avoid (proposal):** Define an independent outcome oracle before implementing named decoders. For CSS code capacity, retain the sampled physical Pauli error and correction; check both syndromes, compute the residual, test exact equality, stabilizer-row-space membership, and its action on a validated independent logical basis. Preserve every boolean and a mutually exclusive outcome label in the event ledger. Test with hand-constructed exact, stabilizer-equivalent, logical, and invalid-syndrome cases. Do not infer logical success from convergence.

**Warning signs:** Logical failure is computed as `not converged`; exact-match rate is called success rate; all converged candidates have the same outcome; a correction with the right syndrome but nontrivial logical action passes a fixture.

**Phase to address:** CSS mathematical contract and outcome oracle, before any curve-reproduction claim.

---

### 2. Losing X/Z correlation or changing quaternary conventions silently

**What goes wrong:** A purported quaternary reproduction actually decodes two binary components independently, maps `Y` inconsistently, or uses marginal X/Z probabilities as if they were independent under depolarizing noise. BPGD specifies a joint four-state prior `(1-p,p/3,p/3,p/3)` for `I,X,Y,Z` and a quaternary guided-decimation rule. **Evidence: MEDIUM** ([BPGD, §6](https://arxiv.org/html/2312.10950v2)).

**Why it happens:** CSS algebra supports separate syndrome equations, but a physical `Y` contributes to both components. Pauli ordering, symplectic sign, check labels, error-rate definition, and hard-decision tie rules vary across papers and libraries.

**How to avoid (proposal):** Put Pauli ordering, `(x,z)` encoding, syndrome/check orientation, `Y` handling, probability parameterization, LLR sign, tie rules, and hard-decision convention in a versioned kernel contract. Sample one four-state Pauli per qubit for correlated noise. Validate analytically on single-qubit and tiny CSS cases, including `Y`. Record whether a paper comparison uses joint quaternary inference or a documented split approximation; do not treat those as the same kernel family.

**Warning signs:** A `Y` fixture produces only one syndrome component; empirical `P(X\cap Z)` equals a product imposed by two independent samplers; a quaternary run reuses the binary decoder's two independent likelihood vectors; results depend on matrix row labels.

**Phase to address:** Correlated quaternary kernel and noise-contract phase; establish shared conventions in the CSS foundation.

---

### 3. Treating circuit detectors as code-capacity syndromes, or omitting observables

**What goes wrong:** A circuit decoder appears to “converge” because it matches detector events, while its predicted logical observable flips are wrong. A generated detector error model may contain correlated symptoms and frame changes; detector indices and observable indices are different namespaces. **Evidence: MEDIUM** ([Stim detector error model specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md), [Relay-BP decoding objects](https://arxiv.org/html/2506.01779v2)).

**Why it happens:** Repeated noisy measurements turn spatial checks into space-time detection events. Circuit fault mechanisms may flip several detectors and logical observables together. Relay-BP formulates this with a check matrix `H` and a separate action matrix `A`; valid `H ê = σ` alone does not establish `A ê = A e`.

**How to avoid (proposal):** In the circuit phase, pin circuit text/hash, detector error model, observable definitions, round count, final perfect round convention, fault decomposition, and decoder input transform. Save true and predicted observable vectors separately from detector parity. Verify on injected single-fault and correlated-fault cases, including faults with the same detector signature but different logical action. Record when an independent-fault approximation or XZ decomposition changes the source model.

**Warning signs:** Circuit ledger has only a syndrome bit; observable count is inferred from detector count; code-capacity parity matrices are reused without a circuit-to-detector mapping; decoder output is scored by detector matching alone.

**Phase to address:** Circuit-level model and observable-oracle phase, after both code-capacity kernels.

---

### 4. Declaring a reproduced curve from visual overlap or too few failures

**What goes wrong:** Zero observed failures are treated as zero logical error rate; a sparse curve is declared matched because plotted markers overlap; tolerance is tuned after seeing the result; many curve points are implicitly treated as one comparison. A fixed-sample binomial interval has a positive upper bound even at zero failures, while simultaneous statements across multiple points need a declared multiplicity policy. **Evidence: MEDIUM** ([NIST proportion intervals](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/propconf.htm), [NIST multiple comparisons](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm)).

**Why it happens:** Logical failures can be rare, published plots may omit shot counts or uncertainty, and log-axis digitization adds extraction error. Comparing point estimates hides all three uncertainties.

**How to avoid (proposal):** Before running, specify each manifest's source point, whether its value came from a table/data file or plot digitization, axes and digitization uncertainty, outcome denominator, simulation cap, interval procedure, and acceptance rule. For fixed-shot Bernoulli sampling, use an exact binomial interval or justified alternative; report zero-failure points as upper bounds. Define the family of points/claims and its multiplicity treatment. Mark a point **inconclusive** when the available shots cannot resolve the claimed tolerance; keep faithful paper settings separate from controlled experiments.

**Warning signs:** `0/N` is plotted as exact zero; no shots/failures are retained per point; digitized marker precision exceeds the figure resolution; tolerance changes after a failed reproduction; only favorable points are reported.

**Phase to address:** Reproduction manifest and statistical acceptance phase, before large simulation campaigns; revisit at manuscript evidence lock.

---

### 5. Applying fixed-sample uncertainty to adaptively stopped sampling

**What goes wrong:** A run stops on a target failure count or is repeatedly inspected, yet a fixed-`N` interval is reported as if sample size had been predetermined. Sinter supports `max_errors` and `max_shots`, and its documentation notes that batching can exceed the nominal error target. Time-uniform confidence sequences exist for arbitrary stopping times. **Evidence: MEDIUM** ([Sinter collection API](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md), [Howard et al., confidence sequences](https://arxiv.org/abs/1810.08240)).

**Why it happens:** Target-failure collection is efficient at small error rates, but its stopping rule is statistically different from a fixed-shot design; HPC resume/early termination adds more stopping states.

**How to avoid (proposal):** Record the planned and realized rule per point: shot cap, failure target, batch overshoot, wall-clock cap, resume history, and actual shots/errors. Use an interval or sequential procedure valid for that design; alternatively predeclare fixed-shot checkpoints and analyze only those checkpoints. Never silently combine partial jobs, adaptive stopping, and fixed-shot error bars. Give every run an explicit completion or censoring status.

**Warning signs:** Every point has exactly the target number of failures but is analyzed with an ordinary fixed-`N` interval; checkpoint plots are repeatedly used to decide whether to stop without a declared rule; `max_errors` is recorded but realized overshoot is not.

**Phase to address:** Simulation harness and statistical acceptance phase.

---

### 6. Biased comparisons from unmatched samples, selection, and postselection

**What goes wrong:** Decoder A sees a different noise sample from decoder B, a slow or nonconverged shot is dropped, or a reported “logical error rate” changes denominator after postselection. Sinter explicitly tracks `shots`, `errors`, and `discards`; its detector and observable postselection modes have different conditions, and observable postselection can use the measured logical value. **Evidence: MEDIUM** ([Sinter task and statistics API](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md)).

**Why it happens:** Reference implementations may have their own sampling loops and failure handling. A conditional error rate among accepted shots and an unconditional failure rate answer different questions. Decoder-specific postselection can break comparability even on shared input shots.

**How to avoid (proposal):** For controlled comparisons, materialize immutable per-shot error/fault samples and IDs, deliver the same ordered samples to every eligible decoder, and keep decoder randomness in independent named streams. Record attempted, completed, accepted, discarded, timed-out, and logically failed counts with reason codes. Report both acceptance probability and conditional error among accepted shots; define an unconditional metric that charges timeout/nonconvergence according to a predeclared rule. Distinguish detector-only operational postselection from oracle-aided observable postselection. Keep paper-faithful denominators when reproducing a paper, with differences documented.

**Warning signs:** Two decoders have different shot IDs at the same curve point; a denominator is simply `shots` despite discards; runtime summaries exclude timeouts; postselected logical errors appear to vanish without acceptance-rate reporting.

**Phase to address:** Event ledger and controlled-comparison harness; circuit phase adds detector/observable postselection semantics.

---

### 7. Comparing branch-heavy algorithms by a single BP iteration count

**What goes wrong:** A sequential relay leg, parallel impulse branch, beam-search path, decimation round, and OSD/LSD fallback are all counted as one “iteration,” giving misleading work and latency rankings. The source algorithms have different composition: Relay-BP passes marginals across legs and selects among valid candidates; impulse decoding can launch many independent BP instances after a failed initial run; BeamSearch branches and prunes paths, reporting both mean and 99.9th-percentile runtime. **Evidence: MEDIUM** ([Relay-BP, §III and algorithm](https://arxiv.org/html/2506.01779v2), [impulse decoding, §IV](https://arxiv.org/html/2606.18240v1), [BeamSearch, §§II–III](https://arxiv.org/html/2512.07057v2)).

**Why it happens:** “Iteration” describes a local update within a specific kernel; it is neither total operations nor critical-path latency across composite policies. Optional postprocessing may dominate cost without changing BP iteration count.

**How to avoid (proposal):** Log per-shot and per-attempt BP calls, edge-message updates or another defined kernel-equivalent work unit, iterations per call, branch/path count, serial depth, candidate count and selection rule, postprocessor calls and elimination work, allocations, runtime, hardware/backend, and precision mode. Report total work, critical-path work, mean/tail wall time, and logical performance separately. Budget-controlled comparisons should cap a declared work unit and state how parallel resources are charged. Include postprocessing-off and on strata where compatible.

**Warning signs:** An impulse shot with 100 branches reports 100 rather than roughly 100 branch-runs worth of iterations; Relay-BP legs disappear from the ledger; a beam width change leaves work unchanged; OSD-on improves performance while cost plots still show BP-only work.

**Phase to address:** Canonical execution/ledger contract before named policy implementations; calibrate work units and timing in each kernel phase.

---

### 8. Assuming matching curves prove matching policy semantics

**What goes wrong:** A policy implementation yields a similar logical-error curve while using different initialization, memory carryover, tie handling, decimation/freeze rule, candidate selection, stopping, or numerical precision. Different mechanisms can produce statistically indistinguishable aggregate curves. The BPGD quaternary algorithm and Relay-BP algorithm specify concrete internal steps, not just target error rates. **Evidence: MEDIUM** ([BPGD, algorithm 3](https://arxiv.org/html/2312.10950v2), [Relay-BP, algorithm 1](https://arxiv.org/html/2506.01779v2)).

**Why it happens:** Numerical traces are sensitive to LLR clipping, infinity approximations, floating-point reduction order, schedule, and random tie breaking. A generic “policy” abstraction can also erase distinctions that require a separate mathematical kernel.

**How to avoid (proposal):** Specify each named policy as a source-linked state transition with inputs, update order, random draws, stopping and selection; record a compatibility matrix by kernel family. Use tiny deterministic trace fixtures and source implementation comparison to check semantics, while accepting statistical rather than bitwise curve agreement as the reproduction criterion. Pin both native reference precision and canonical precision; label differences instead of silently changing either. Treat a numerically different but statistically matching curve as curve reproduction only until policy semantics are separately validated.

**Warning signs:** A policy name has parameters but no equations or order of operations; all policies can be freely composed with every kernel; canonical and reference curves agree but candidate/trace behavior contradicts the paper; changing float precision or tie rules alters decisions without provenance.

**Phase to address:** Policy semantics and compatibility contract, then source-grounded implementation of each named policy.

---

### 9. Building a reproduction registry on moving or ambiguous references

**What goes wrong:** A reference package or paper revision changes, while old manifests still claim to reproduce the same experiment. The `bp_osd` repository notes a rewrite and relocation of most implementation into `ldpc`, and the Sinter main-branch API calls itself a development version. **Evidence: MEDIUM** ([BP-OSD repository](https://github.com/quantumgizmos/bp_osd), [Sinter API notice](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md)).

**Why it happens:** Paper names, package names, Git branches, algorithm variants, and default parameters are not stable identities. A result curve alone cannot recover code construction, logical-operator basis, software revision, or reference settings.

**How to avoid (proposal):** Give each experiment an immutable manifest with paper version/figure, source repository and commit/tag, dependency lock, source-defined algorithm variant, code and logical-operator hashes, circuit/DEM hashes where relevant, noise, seeds, budgets, outputs, tolerances, and discrepancy notes. Separate source fact, interpretation, and canonical adaptation in the mapping registry. Revalidate a small fixture on dependency updates. Resolve SI/OTF/LSD and other abbreviated mechanisms from each primary source before claiming support.

**Warning signs:** A manifest says only `latest`; code hash exists but logical-operator hash does not; two figures share a name but differ in noise or decoder defaults; a dependency upgrade changes a reference curve unnoticed.

**Phase to address:** Systematic mapping protocol and executable manifest registry from the first phase onward; reference integration in the relevant decoder phases.

## Technical Debt Patterns

| Shortcut | Immediate benefit | Long-term cost | When acceptable |
|----------|-------------------|----------------|-----------------|
| Keep only aggregate failures and mean iterations | Small result files | Cannot reconstruct logical classes, censoring, postselection, or work distributions | Never for production experiments; acceptable only in throwaway kernel smoke tests |
| Treat every algorithm as an adapter behind one interface | Fast demos | No auditable shared policy semantics or compatibility boundaries | Only for explicitly labeled executable references |
| Use default float precision and implicit tie rules | Faster port | Different decisions and unverifiable reference/canonical discrepancies | Only when precision and tie behavior are recorded and tested |
| Digitize figures without extraction metadata | Fills missing tables | False precision in reproduction targets | Exploratory mapping only, not final acceptance |

## Integration Gotchas

| Integration | Common mistake | Correct approach |
|-------------|----------------|------------------|
| Stim/Sinter | Confuse detector bits, observable flips, and postselected discards | Pin versions; test detector/observable indexing and report all three counters |
| BP-OSD/BP-LSD and Relay-BP references | Assume package defaults or `main` match the cited paper | Pin source revision and exact flags; preserve native outputs and discrepancy notes |
| Canonical policy engine | Translate a named algorithm from its curve legend | Encode source-defined state transitions and compatibility predicates, then verify traces |

## Performance Traps

| Trap | Symptoms | Prevention | When it breaks |
|------|----------|------------|----------------|
| Full per-edge trace on every Monte Carlo shot | I/O and storage dominate decode time | Use compact shot ledger plus sampled detailed traces, with immutable IDs | Large rare-failure sweeps |
| Enumerating all branches without a cap | Work grows with beam width, decimation depth, or impulse nodes | Explicit branch/round/work caps and censoring reason | Larger codes and circuit Tanner graphs |
| Comparing only mean runtime | Tail latency hidden by many easy syndromes | Report quantiles and timeout fraction with the hardware/backend | Circuit-level or real-time claims |

## “Looks Done But Isn't” Checklist

- [ ] **Outcome oracle:** Test syndrome-valid logical failure, exact success, stabilizer-degenerate success, and invalid syndrome separately.
- [ ] **Correlated noise:** Show `Y` exercises both X and Z components and the declared four-state prior.
- [ ] **Circuit result:** Score predicted logical observables independently of detector parity.
- [ ] **Reproduction:** Provide source point, shots, failures, uncertainty, stopping rule, digitization provenance if used, and predeclared acceptance tolerance.
- [ ] **Controlled comparison:** Verify identical shot IDs/noise samples, explicit work cap, and paired outcomes across eligible decoders.
- [ ] **Censoring:** Account for timeout, no candidate, nonconvergence, postselection, and partial jobs in denominators and runtime.
- [ ] **Policy identity:** Match source state transitions and versioned reference settings; curve agreement alone does not close this check.

## Recovery Strategies

| Pitfall | Recovery cost | Recovery steps |
|---------|---------------|----------------|
| Wrong outcome oracle or lost physical errors | HIGH | Freeze publication claims; fix oracle; rerun all affected shots if physical-error/candidate records are missing |
| Wrong quaternary/circuit convention | HIGH | Correct model contract and hashes; invalidate and rerun affected experiments |
| Missing stopping, discard, or work provenance | HIGH | Recover from raw shot/checkpoint logs if possible; otherwise rerun with ledger enabled |
| Reference/version drift | MEDIUM | Pin old revision, reproduce fixture, then separately qualify upgraded reference |
| Digitized-only target | MEDIUM | Obtain source data or widen/qualify target uncertainty; mark unresolved when evidence is insufficient |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention phase | Verification gate |
|---------|------------------|-------------------|
| Outcome conflation | CSS mathematics and oracle | Constructed residual/coset fixtures |
| Quaternary convention drift | Correlated quaternary kernel | Single-Pauli and tiny-code joint-noise fixtures |
| Detector/observable confusion | Circuit-level model | Injected faults with known detector and observable flips |
| Weak curve acceptance; optional stopping | Manifest/statistical acceptance | Predeclared interval/stopping examples, including zero failures |
| Unpaired or selected comparisons | Shared-sample harness and ledger | Shot-ID equality and denominator audit |
| Hidden branch and postprocessor work | Canonical execution and named policies | Additive work counters for relay, impulse, beam, and OSD-on/off |
| Policy and reference drift | Mapping registry and policy specifications | Pinned version plus trace/fixture review |

## Sources and Scope

The following are primary papers or official project/statistical documentation consulted for this initial scoping. Their presence here does **not** constitute a completed systematic search, quality appraisal, or final selection of publication experiments.

1. [Yao et al., *Belief Propagation Decoding of Quantum LDPC Codes with Guided Decimation*, arXiv:2312.10950v2](https://arxiv.org/html/2312.10950v2) — 2024 revision; outcome categories, CSS and quaternary conventions, decimation.
2. [Müller et al., *Improved belief propagation is sufficient for real-time decoding of quantum memory*, arXiv:2506.01779v2](https://arxiv.org/html/2506.01779v2) — 2025 revision; Relay-BP state, legs, solution selection, circuit action matrix.
3. [Bhatnagar et al., *Impulse Decoding of Quantum LDPC Codes*, arXiv:2606.18240v1](https://arxiv.org/html/2606.18240v1) — June 2026; parallel shortening branches and work structure.
4. [Ye et al., *Beam search decoder for quantum LDPC codes*, arXiv:2512.07057v2](https://arxiv.org/html/2512.07057v2) — 2025 revision; branch/prune policy and runtime tails.
5. [Stim detector error model specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md) — detector symptoms, logical observable frames, correlated mechanisms.
6. [Sinter development API](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md) — shot/error/discard fields, postselection, shot/error stopping; pin a release before implementation.
7. [NIST proportion confidence intervals](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/propconf.htm) — exact binomial interval basis for rare/zero failures under fixed sampling.
8. [Howard et al., *Time-uniform, nonparametric, nonasymptotic confidence sequences*, arXiv:1810.08240](https://arxiv.org/abs/1810.08240) — sequential uncertainty under optional stopping.
9. [NIST Bonferroni multiple-comparison guidance](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) — simultaneous interval policy across curve points/claims.
10. [Quantumgizmos BP-OSD repository](https://github.com/quantumgizmos/bp_osd) — documents the implementation rewrite and why source revision matters.

**Unresolved for phase research:** Paper-specific sample counts and original curve data; exact reference commits; statistical acceptance threshold; native/canonical precision and operation-count calibration; code and logical-operator serialization/hashing; circuit fault-model approximations; detailed SI/LSD/OTF semantics. Resolve these with the mapping study and per-phase source/code inspection rather than treating this document as a completed review.

---
*Pitfalls research for: policy-based BP-family QLDPC research platform*
