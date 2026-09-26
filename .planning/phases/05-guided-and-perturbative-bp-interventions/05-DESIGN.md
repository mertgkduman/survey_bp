# Phase 5 preparatory design: guided and perturbative BP

Date: 26 September 2026. Status: proposed contracts; production execution has
not started. Phase 4 remains active. Requirements: MOD-02, MOD-03, INT-01,
INT-02, INT-03, INT-04.

## 1. Research boundary and source decisions

This design extends the canonical binary CSS engine. It introduces explicit
changes to priors, constraints and attempt state while keeping the original
observation immutable. It does not implement a second BP engine or substitute
a native decoder for canonical policy execution.

Primary sources: [BPGD, arXiv:2312.10950v2, Section 4.3 and Algorithm 1](https://arxiv.org/html/2312.10950v2)
and [impulse decoding, arXiv:2606.18240v1, Section IV and Algorithm 1](https://arxiv.org/html/2606.18240v1).
The versioned source-status record is
`docs/evidence/phase5-source-status-20260926.json`.

BPGD alternates SPA rounds and reliability-guided changes to channel priors;
the reported finite magnitude is 25. Algorithm 1 assigns zero posterior bias
to positive prior, whereas Equation 36 assigns it negative prior. Its last
decimation is followed by return, without another explicit BP call. We propose
an Algorithm-1 interpretation with declared zero and final-round rules.
Continuing message state is an inference requiring native confirmation.

Impulse first tries BP, then independently shortens variables to one on
nonconvergence and ranks converged candidates by Hamming weight. Its
first-convergence alternative uses declared index order. Structural shortening
below is our proposed exact-constraint realization; matching native numerical
trajectories remains a separate question.

Neither source's native-code identity has been verified in this update.
Syndrome/sign-flip source variants also remain unresolved. Their general
contract below is ready for implementation planning, but a named source claim
requires an equation, version and availability record first.

## 2. Objects and boundaries

| Proposed object | Required contents and invariant |
| --- | --- |
| InterventionSpec | Source variant, trigger, eligible targets, operator, value, lifetime, reset, budget and ordering |
| WorkingProblemVNext | Original identity, transformed H and syndrome, ordered column/row maps, transformation and lift identities |
| FixationMap | Unique original indices, binary values, parent map, lifetime and release rule |
| BpSessionState | Graph/prior identities, messages, beliefs, histories, schedule cursor, dtype and committed-unit index |
| InterventionProposal | Before-state identity, target, proposed new state/view, reserved work and child lineage |
| LiftMap | Total deterministic reconstruction to original coordinates and any algebraic certificate |
| CandidateValidation | Working validity, lift result, independent original-syndrome validity and rejection reason |
| RestartSpec | Preserved fields, reset fields, attempt cap, stream identity and stopping scope |

Use a new public schema and versioned ledger grammar for these additions.
Historical manifests and ledgers retain their meanings. Policy-visible views
contain only the original observation, allowed graph/priors and committed
decoder state. Hidden physical errors and logical outcomes remain exclusively
in the independent evaluator. Selection never inspects logical truth.

The main engine currently initializes a new attempt; it has no admitted
transformed `WorkingProblem`. A round/session API must make continuation an
explicit operation rather than reconstructing messages from an output vector.

## 3. Finite bias and exact fixing

`finite_prior_bias` assigns a finite signed prior to a selected original index,
marks it ineligible for another decimation, and leaves the graph unchanged.
It does not promise that every subsequent hard decision equals that sign.
`hard_constraint` fixes a bit algebraically, changes the working graph and
provides a lift. Neither operator is an alias for the other. Clipping infinity
to a numerical bound is an explicitly labeled approximation.

For BPGD, propose reliability `abs(posterior_llr)`, eligibility among undecimated
indices, stable original-index ties and positive prior for zero under the
Algorithm-1 interpretation. Reliability ordering is equivalent to binary
marginal confidence for finite LLRs. Reject NaN; declare infinity handling.
Fixation persists through its declared search lifetime. Each BP round runs at
most T whole admitted units and checks original validity at declared
boundaries. A within-round early stop and an extra final BP round are separate
adaptations, not implicit optimizations. Specify message continuation and
recomputed belief/prior dependencies before admitting a source variant.

Hard fixing has eligible original indices, binary values and release/reset
events. A release creates a child working view from the immutable original
problem and remaining fixations; it does not edit a parent graph in place.

## 4. Exact shortening and lifting

The following is an independent GF(2) derivation of the proposed contract.
Partition original columns into fixed F and retained R, with fixed values a.
For original equation H c = s, define:

```
H_work = H[:, R]
s_work = s XOR (H[:, F] a)
lift(y)[F] = a
lift(y)[R] = y
```

Then `H_work y == s_work` if and only if `H lift(y) == s`, provided ordered
maps and fixed values match the certificate. Independent original validation
is still mandatory: it detects incorrect maps or corrupted lift records.

After shortening, an empty check with residual one is an immediate
contradiction. An empty check with residual zero may be retained or removed
only with an explicit row map. If all variables are fixed, construct and
validate the unique lifted candidate without inventing a BP iteration.
Dependent rows and inconsistent original syndromes must remain visible.

`tools/validate_intervention_design.py` enumerates all binary 2-by-3 matrices,
syndromes, fixed subsets, fixed values and free candidates. It independently
checks 16,384 shortening/lifting cases. This proves the enumerated finite
fixtures, not arbitrary decoder behavior or a published performance claim.

## 5. Impulse attempt controller

Trigger on baseline nonconvergence/original-syndrome invalidity observable to
the decoder. A valid recovery with wrong hidden logical action cannot trigger
an intervention. Preserve the baseline diagnostic candidate even if rejected.

Each attempted index gets an immutable clone of the declared baseline prior
and its own working view, fresh BP state and attempt identity. The proposed
exact shortening path fixes that index to one. A source implementation using
infinite priors needs an explicit numerical convention and separate fidelity
assessment. Preserve every failed, contradictory and denied attempt.

Lift and original-validate each candidate before selection. Minimum-weight
selection uses original-coordinate Hamming weight, followed by stable declared
attempt/index order and local candidate order. First-convergence selection
returns the earliest eligible declared attempt, regardless of worker arrival;
either await all earlier attempts or execute in that order. A parallel race
mode would be a different, explicitly named adaptation.

## 6. Syndrome and sign perturbations

A syndrome flip creates `s_work = s XOR d` and retains s. A working-valid y
does not become an eligible original recovery by relabeling its syndrome.
Default handling lifts by coordinate identity and rejects it if original
validation fails. If a supplied correction t satisfies `H t = d`, a certified
lift `c = y XOR t` restores the original equation. A row mask alone is not this
certificate. A generic solver that manufactures t adds separately declared
work and belongs to an explicit policy, not silent validation.

A sign perturbation declares which object changes: channel prior, V2C, C2V or
posterior; target selection, magnitude, sign/zero convention and trigger are
mandatory. It also declares whether outgoing messages and cached beliefs are
recomputed, retained or invalidated. Flipping a prior does not automatically
flip stored messages. Until a primary source is resolved, these are research
adaptation operators without a named source-faithful variant.

The retained design fixtures include a working-valid/original-invalid syndrome
flip and the valid certified lift, plus an all-fixed contradiction. They also
show that a finite signed prior can be outweighed by incoming messages.

## 7. Restarts, continuation and randomness

The default restart resets messages, beliefs, schedule cursor, residual cache
and private memory histories. Preservation is allowed only for named fields
with compatible graph, coordinate, prior, dtype and ownership identities.
BPGD round continuation is a separate declared transition. Graph changes
invalidate edge-indexed histories unless a checked mapping is provided.

Streams derive from root identity plus decoder, intervention, attempt and
purpose namespaces. Physical sampling uses its independent namespace and
cannot be consumed by ranking, branching or restarts. Replays record stream
identity and realized draws. Worker count and scheduling do not change draws.
When a failed run has a diagnostic candidate but no reliability field, a
reliability-driven policy must fail clearly or use a prespecified alternative;
it cannot invent a posterior. No-proposal is retained as its own terminal kind.

## 8. Atomicity, provenance and work

Reserve the declared unit before changing graph, priors, histories, ordering
or random cursors. Validate the proposal, compute in private state and commit
the child state plus events together. Budget denial leaves the parent intact.
Numerical failure retains the last committed diagnostic state and records
failed work according to its explicit accounting contract.

Retain links from original -> transformation -> working view -> attempt ->
candidate -> lift -> original validation -> selection -> evaluation. Event
payloads include source variant, target/value, parent state, map/certificate,
reset/preservation rules, proposal and committed state digests, budget scope,
denied work, actual work and terminal reason. Independent replay reconstructs
semantics as well as hashes.

Count BP calls, C2V/V2C elements, belief assemblies, ranking scans, fixation
actions, transformations, lifted coordinates and original checks separately.
Aggregate actual leaf work once across restarts/attempts. A parent's subtotal
is not an additional leaf contribution. Contradiction checks cost real work
but no BP calls. Record setup, decode, lifting/validation, serialization and
analysis boundaries independently; retain absent native counters as missing.

## 9. Evaluation and timing contract

Use matched physical samples with finite, prespecified attempt/work/shot/time
caps and disjoint development/calibration/evaluation namespaces. Freeze
coefficients and tie rules before outcomes. Include every admitted shot in
all-shot failure LER, counting absent selected recovery as failure. Report
valid-correct, valid-wrong-logical, invalid-correct-logical-projection,
invalid-wrong-logical-projection and no-proposal separately. The invalid
projection cells are basis-dependent diagnostics, not successful recovery.

For runtime, time both implementations from an already constructed decoder
input to a returned raw candidate. Separate preparation and independent
validation. Match update algorithm, numerical bounds, stopping, state,
threads and work limits; counterbalance call order and disclose warmup.
Report work distributions and outcomes alongside latency. Even then, a
language-only causal claim needs implementation controls beyond a single
Rust/Python pair. Do not tune settings on the runtime evaluation samples.

## 10. Gates and later reuse

The task map in `05-DESIGN-TASKS.md` covers each Phase 5 requirement and success
criterion. Source discovery, interface sketches and finite algebra validation
can proceed now. Production Phase 5 execution requires completed Phase 4 and
checked plans; named variants additionally require their source decisions.
Source gaps remain visible rather than passing by an invented approximation.

Phase 6 may reuse working views, lifts and attempt lineage for search, but
generic beam execution and voting remain its own work. Quaternary state and
circuit observations require their mathematically compatible engines and
later qualification. No CSS intervention result establishes those regimes.
