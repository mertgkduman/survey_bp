# Phase 10: Correlated Quaternary Execution - Research

**Researched:** 2026-10-06  
**Domain:** Four-state Pauli belief propagation, joint Pauli channels, and source-backed quaternary BP policies  
**Confidence:** MEDIUM — repository facts were read from source files (HIGH); mathematical recommendations come from primary papers retrieved through the configured `websearch` seam, whose verified tier is MEDIUM.

## Summary

Phase 10 should add a second canonical kernel family for four-state Pauli variables. The recommended baseline is Lai and Kuo's scalar log-domain BP: each qubit retains a three-component identity-referenced LLR belief for `X`, `Y`, and `Z`, while each Tanner edge passes the scalar likelihood that the qubit error commutes rather than anticommutes with that edge's Pauli label. This retains the joint `I/X/Y/Z` prior, including the shared `Y=(X,Z)` event, and has a source-stated equivalence to the refined linear-domain BP4 for qubits. [CITED: https://arxiv.org/html/2104.00304]

The scalar implementation must be verified against two deliberately independent references: conventional four-vector BP4 on tiny graphs and exact enumeration of all `4^n` Pauli assignments on very small problems. Kuo and Lai give both conventional vector equations and the refined scalar equations, while also stating that the scalar algorithm has the same output as conventional BP4. [CITED: https://arxiv.org/html/2002.06502] The exact oracle is a project validation recommendation, not a production decoder. [ASSUMED]

The public Phase 10 path should compile immutable Pauli checks, declared joint priors, and the full ordered syndrome into a quaternary problem; sample one categorical Pauli value per qubit; run only compositions admitted by a quaternary compatibility matrix; emit Pauli candidates plus four-state marginals; and hand candidates and hidden truth to an independent evaluator. This follows the repository's existing separation of decoder-visible observation and hidden truth and its four CSS outcome meanings. [VERIFIED: src/bp_registry/sampling.py:16-40; src/bp_registry/evaluator.py:13-19,33-83]

**Primary recommendation:** Build a source-defined scalar LLR-BP4 kernel with a conventional vector BP4 test oracle, then add source-literal Q-BPGD as a quaternary intervention over four-state marginals; reject every binary policy lacking a quaternary derivation rather than porting it by name. [CITED: https://arxiv.org/html/2104.00304] [CITED: https://arxiv.org/html/2312.10950v2]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Pauli/stabilizer algebra and CSS compilation | Model compiler | Independent evaluator | The compiler owns typed immutable checks; the evaluator recomputes syndrome and equivalence independently. [VERIFIED: .planning/research/ARCHITECTURE.md:51-60] |
| Joint four-state BP | Canonical kernel | Policy controller | The kernel owns commutation-factor message math; schedules and interventions select when state advances. [VERIFIED: .planning/research/ARCHITECTURE.md:54-57] |
| Joint channel sampling | Experiment runner | Evidence ledger | Sampling owns physical randomness and hidden truth; the ledger records the resolved prior and sample identity. [VERIFIED: .planning/research/ARCHITECTURE.md:58-60] |
| Q-BPGD | Policy controller | Canonical kernel | The controller chooses an undecimated variable and changes its prior; the kernel supplies four-state marginals without knowing hidden truth. [CITED: https://arxiv.org/html/2312.10950v2] |
| Exact/degenerate/logical classification | Independent evaluator | Model compiler | Outcome classification requires original checks, logical basis, and hidden truth, all outside decoder visibility. [VERIFIED: src/bp_registry/evaluator.py:33-83] |
| Manifests, trace, replay, and work | Evidence ledger | Experiment runner | Project architecture assigns provenance and final evaluation to the runner/evaluator boundary, while the kernel emits typed work and state events. [VERIFIED: .planning/research/ARCHITECTURE.md:59-73] |

<phase_requirements>
## Phase Requirements

The requirement text below is quoted verbatim from the source of truth. [VERIFIED: .planning/REQUIREMENTS.md:134-139]

| ID | Description | Research Support |
|----|-------------|------------------|
| QBP-01 | “A researcher can execute a canonical four-state Pauli BP kernel using source-defined commutation factors, message representation, numerical conventions, and joint X/Z inference.” [VERIFIED: .planning/REQUIREMENTS.md:136] | Sections **Canonical Mathematical Contract**, **Numerical Contract**, and **Validation Architecture** specify the source equations, representation, and differential oracles. |
| QBP-02 | “A researcher can sample a declared joint I/X/Y/Z channel, including correlated X/Z behavior, and verify priors, error-rate conventions, and Y-error fixtures.” [VERIFIED: .planning/REQUIREMENTS.md:137] | Section **Joint Pauli Sampling Contract** specifies one categorical draw per qubit, analytic correlation identities, and deterministic I/X/Y/Z fixtures. |
| QBP-03 | “Quaternary outputs pass independent syndrome, exact/degenerate/logical-outcome checks against the common code-capacity mathematical conventions.” [VERIFIED: .planning/REQUIREMENTS.md:138] | Section **Independent Evaluation Contract** maps Pauli values to independent symplectic checks and preserves the existing four outcome names. |
| QBP-04 | “A researcher can run source-backed compatible policy compositions in the quaternary kernel, including the published quaternary BPGD case, with unsupported ports explicitly rejected or labeled new adaptations.” [VERIFIED: .planning/REQUIREMENTS.md:139] | Sections **Policy Compatibility Matrix** and **Q-BPGD Contract** identify admitted source policies, source-literal semantics, and closed rejection behavior. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

The following actionable directives are quoted from `AGENTS.md` and must be treated as planning constraints. [VERIFIED: AGENTS.md:11-21,41-49,55-64,77-87]

- “One canonical execution engine per mathematically compatible kernel family.” [VERIFIED: AGENTS.md:13]
- “BP-internal policies and named BP modifications before optional OSD/LSD-style postprocessing.” [VERIFIED: AGENTS.md:14]
- “CSS code-capacity before correlated quaternary code-capacity before circuit-level decoding.” [VERIFIED: AGENTS.md:15]
- “Statistical agreement with published curves is sufficient,” with discrepancies documented. [VERIFIED: AGENTS.md:16]
- “Every simulation must emit an event ledger, and every supported paper must have a reproduction manifest.” [VERIFIED: AGENTS.md:17]
- Preserve both paper-specific and controlled configurations. [VERIFIED: AGENTS.md:18]
- Cite primary mathematical sources; record interpretations and unresolved source details; do not replace algebraic and policy checks with curve agreement. [VERIFIED: AGENTS.md:45-47]
- Preserve approved workflow/model settings, keep all three regimes in the journal milestone, and keep BP modifications ahead of substantial optional fallback work. [VERIFIED: AGENTS.md:48-49]
- Keep original problems immutable; keep hidden truth outside policies; evaluate outputs independently; and record equations, order, compatibility, numerics, stopping, lineage, and work. [VERIFIED: AGENTS.md:59-63]
- Distinguish source-faithful reproduction, canonical adaptation, controlled comparison, and mapped-only evidence. [VERIFIED: AGENTS.md:64]
- Repo changes must begin through a GSD workflow; this research was dispatched through `$gsd-plan-phase` and makes no implementation edits. [VERIFIED: AGENTS.md:77-87]

## Current Repository Baseline and Required Boundary

### What can be reused

The repository already pins Python `>=3.12` and the exact dependency string `dependencies = ["numpy==2.2.6", "scipy==1.17.1", "ldpc==2.4.1", "pydantic==2.13.5"]`. [VERIFIED: pyproject.toml:5-10] The new canonical kernel can therefore use the existing NumPy `float64` and strict Pydantic manifest conventions without adding a runtime package. [VERIFIED: pyproject.toml:9-10; src/bp_registry/canonical/contracts.py:12-18]

The current numerical layer already contains a stable ordered `boxplus_pair`, an ordered `boxplus` fold, finite saturation, explicit syndrome sign, and exact-zero binary hard decisions. [VERIFIED: src/bp_registry/canonical/numerics.py:15-41,52-62,95-146] Reuse the arithmetic primitive only through a new quaternary numerical profile; the existing profile is verbatim `profile_id="binary-spa-flooding-f64-v1"`, `saturation=25.0`, and `exact_zero_decision=0`, so silently inheriting its full semantics would mislabel the new kernel. [VERIFIED: src/bp_registry/canonical/numerics.py:15-36]

The work schema already counts verbatim `check_to_variable_updates`, `variable_to_check_updates`, `belief_assemblies`, `candidate_constructions`, `convergence_checks`, `bp_calls`, `candidate_checks`, `intervention_actions`, `fixation_actions`, and `original_checks`, among other atomic categories. [VERIFIED: src/bp_registry/canonical/budgets.py:18-44] Those categories can cover Q-BP and Q-BPGD if each count's unit is documented as an edge message, four-state belief assembly, Pauli hard decision, or fixation; schema changes are unnecessary unless planners decide to count scalar arithmetic separately. [ASSUMED]

The evaluator already defines the outcome union verbatim as `"invalid_syndrome", "exact", "stabilizer_equivalent", "logical_failure"` and checks both X and Z residuals against original CSS checks and logical operators. [VERIFIED: src/bp_registry/evaluator.py:13-19,33-83] Preserve those names for Phase 10 evidence. [VERIFIED: .planning/ROADMAP.md:531-534]

### What must remain a separate kernel family

The existing `OriginalProblem` contains verbatim fields `lineage_id`, `hx`, `hz`, and `syndrome`, and validates the syndrome length against `hz.shape[0]`; `WorkingProblem` defaults to the single binary matrix `original.hz`. [VERIFIED: src/bp_registry/canonical/problems.py:20-32,35-85] It cannot represent an ordered full stabilizer matrix with X/Y/Z edge labels and the combined syndrome without changing its mathematical meaning. Create a quaternary problem type rather than widening these binary fields. [VERIFIED: .planning/ROADMAP.md:531-537]

The existing candidate is a binary one-dimensional array whose length is checked against `original.hz.shape[1]`. [VERIFIED: src/bp_registry/canonical/problems.py:88-98] A quaternary candidate needs an explicit Pauli representation and an independently convertible symplectic pair. [CITED: https://arxiv.org/html/2312.10950v2]

The current sampler draws `hidden_x` and `hidden_z` from separate random calls using separate scalar rates. [VERIFIED: src/bp_registry/sampling.py:76-118] That produces an independent product channel and cannot represent an arbitrary declared joint `I/X/Y/Z` prior; it must not be used as the Phase 10 physical sampler. [VERIFIED: .planning/REQUIREMENTS.md:137]

The existing policy registry admits the verbatim update kinds `"identity", "binary_spa", "min_sum", "normalized_min_sum", "offset_min_sum"` and schedule kinds `"identity", "flooding", "layered", "check_node_serial", "variable_node_serial", "residual", "randomized", "group_shuffled"`. [VERIFIED: src/bp_registry/canonical/contracts.py:62-73] A Phase 10 contract must define a separate closed set; accepting these names automatically would violate the project's compatibility boundary. [VERIFIED: .planning/research/ARCHITECTURE.md:77-88]

## Standard Stack

### Core

| Library/runtime | Version | Purpose | Why Standard |
|-----------------|---------|---------|--------------|
| Python | `>=3.12`; probed `3.12.2` | Typed reference implementation and orchestration | This is the declared project runtime and installed interpreter. [VERIFIED: pyproject.toml:9; environment probe 2026-10-06] |
| NumPy | `2.2.6` | Immutable Pauli arrays, sparse edge buffers, categorical sampling, stable log arithmetic | Already pinned and installed; `numpy.logaddexp` computes log-sums without returning to probability scale. [VERIFIED: pyproject.toml:10; environment probe 2026-10-06] [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html] |
| SciPy | `1.17.1` | Independent sparse/linear-algebra checks where existing project utilities require it | Already pinned and installed; do not add a new finite-field dependency for four Pauli symbols. [VERIFIED: pyproject.toml:10; environment probe 2026-10-06] |
| Pydantic | `2.13.5` | Strict, frozen manifest and policy validation | Already pinned; current contracts use `extra="forbid"`, `strict=True`, `frozen=True`, and `allow_inf_nan=False`. [VERIFIED: pyproject.toml:10; src/bp_registry/canonical/contracts.py:12-18] |

### Supporting

| Tool/reference | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| pytest | `9.0.3` installed | Unit, differential, replay, and public execution gates | Use from Wave 0 through the phase gate. [VERIFIED: environment probe 2026-10-06] |
| Kuo author C reference | commit `402a83e8afd0df5203693aeeed1e42f1900e344d` | Optional isolated reference inspection for MBP-family behavior | Treat as a GPL reference environment, not a canonical dependency or a Yao Q-BPGD implementation. [CITED: https://github.com/kywukuo/qLDPC_dec/tree/402a83e8afd0df5203693aeeed1e42f1900e344d] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Scalar log-domain BP4 production kernel | Conventional four-vector probability-domain BP4 | The vector equations are direct and valuable as a tiny-graph oracle, but the primary paper reports greater check-node complexity; keep it out of the production execution path. [CITED: https://arxiv.org/html/2002.06502] |
| Explicit Pauli commutation algebra | A third-party GF(4) package | The factor only needs Pauli commutation parity, and another package would add identity, licensing, and representation risk without replacing the independent oracle. [CITED: https://arxiv.org/html/2104.00304] |
| New quaternary problem/candidate types | Coercing Pauli values through the binary `OriginalProblem` | Coercion loses the full syndrome and joint state meaning documented above. [VERIFIED: src/bp_registry/canonical/problems.py:20-98] |

**Installation:** No package installation is recommended for Phase 10; retain the current project environment. [VERIFIED: pyproject.toml:5-22]

**Version verification:** `pip index versions` confirmed the pinned releases on 2026-10-06. PyPI JSON reported first file upload times: NumPy `2.2.6` on `2025-05-17`, SciPy `1.17.1` on `2026-02-23`, Pydantic `2.13.5` on `2026-08-28`, and pytest `9.0.3` on `2026-04-07`. [VERIFIED: PyPI registry probes 2026-10-06] Newer NumPy, SciPy, and pytest releases exist, but dependency upgrades are outside this phase and should not be mixed into the scientific change. [VERIFIED: PyPI registry probes 2026-10-06]

## Package Legitimacy Audit

No external package is added, so the Package Legitimacy Gate is not triggered. [VERIFIED: Standard Stack recommendation above] The Kuo repository is an isolated source reference and is not installed or imported by the canonical runtime. [CITED: https://github.com/kywukuo/qLDPC_dec]

## Canonical Mathematical Contract

### Pauli representation and syndrome

Yao et al. define the numeric order verbatim as “0,1,2,3 representing the absence of error, or the presence of a Pauli σx, σy or σz error.” [CITED: https://arxiv.org/html/2312.10950v2] Persist that order as `I=0, X=1, Y=2, Z=3`; never infer it from an array position at an API boundary. [CITED: https://arxiv.org/html/2312.10950v2]

Represent each Pauli independently as symplectic bits with `I=(0,0)`, `X=(1,0)`, `Y=(1,1)`, `Z=(0,1)`, following `Y=iXZ` and Yao's `D(a,b)` definition. [CITED: https://arxiv.org/html/2312.10950v2] For an error `(x,z)` and stabilizer matrix `H=[H_x,H_z]`, compute the syndrome as `s=(x,z) Λ H^T`, equivalently the rowwise commutation parity. [CITED: https://arxiv.org/html/2312.10950v2]

The Pauli Tanner graph has an edge exactly where a stabilizer entry is not identity, and each edge carries label `X`, `Y`, or `Z`. [CITED: https://arxiv.org/html/2002.06502] The typed edge table must therefore include check index, qubit index, and Pauli label in its semantic hash. [ASSUMED]

Compile current CSS artifacts losslessly: rows of `hx` become X-labeled stabilizer rows, rows of `hz` become Z-labeled stabilizer rows, and the combined syndrome order is declared in the artifact rather than inferred. Existing code defines `hx`/`hz`, verifies `hx @ hz.T == 0`, and labels `Hz eX` as a Z-check observation and `Hx eZ` as an X-check observation. [VERIFIED: src/bp_registry/css.py:64-107,160-163; src/bp_registry/sampling.py:105-114] The exact concatenation order is a new persisted convention and must be locked before implementation. [ASSUMED]

### Recommended production message representation

For each qubit `n`, store the three identity-referenced LLRs

`Λ_n^W = log(P(E_n=I) / P(E_n=W))`, for `W in {X,Y,Z}`. [CITED: https://arxiv.org/html/2104.00304]

For edge Pauli `η`, quantize a three-component LLR belief to the scalar commutation LLR

`λ_η(Γ) = log(P(<E_n,η>=0) / P(<E_n,η>=1))`. [CITED: https://arxiv.org/html/2104.00304]

For check `m`, edge `(m,n)`, and syndrome bit `z_m`, compute

`Δ_{m→n} = (-1)^{z_m} boxplus_{n' in N(m)\{n}} λ_{H_mn'}(Γ_{n'→m})`. [CITED: https://arxiv.org/html/2104.00304]

For each nonidentity Pauli `W`, compute the excluded variable message

`Γ_{n→m}^W = Λ_n^W + Σ_{m' in M(n)\{m}, <W,H_m'n>=1} Δ_{m'→n}`. [CITED: https://arxiv.org/html/2104.00304]

The posterior uses the same sum without excluding `m`; decide `I` if all three identity-referenced LLRs are positive, otherwise choose the nonidentity Pauli with minimum LLR, then test the original syndrome. [CITED: https://arxiv.org/html/2104.00304] An exact-zero/equal-minimum rule is not specified in the consulted algorithm text, so the manifest must persist a project tie rule and label it an interpretation. [ASSUMED]

For qubits (`q=2`), the paper states that this LLR algorithm is equivalent to the refined linear-domain BP4 and that schedules other than parallel, including serial, are permitted. [CITED: https://arxiv.org/html/2104.00304]

### Independent vector BP4 oracle

Implement conventional probability-vector BP4 only in test/reference code. A V2C message is a normalized distribution over `I/X/Y/Z`; the C2V component for candidate `W` sums products over neighboring assignments whose total commutation parity matches the check syndrome; V2C then multiplies the prior by all other C2V components and normalizes. [CITED: https://arxiv.org/html/2002.06502]

On cycle-free tiny graphs and matched priors, assert agreement among vector BP4, scalar LLR-BP4, and exact enumeration to a prespecified tolerance. The source states BP is exact on a tree and the scalar implementation is output-equivalent to conventional BP4. [CITED: https://arxiv.org/html/2104.00304] [CITED: https://arxiv.org/html/2002.06502]

### Numerical Contract

Use `float64`, ordered edge reductions, stable pairwise box-plus, and log-sum-exp for commutation/anticommutation groups. The source recommends Jacobian-logarithm computation, and NumPy documents `logaddexp` for adding probabilities represented in log form. [CITED: https://arxiv.org/html/2104.00304] [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]

Do not use the all-neighbor `boxminus` shortcut in the correctness path. The source warns that the shortcut may be approximate because a zero input requires a tiny disturbance. [CITED: https://arxiv.org/html/2104.00304]

Persist a quaternary numerical profile containing dtype, LLR orientation, saturation, zero/tie rule, reduction order, normalization, and nonfinite policy. The source equations require real LLRs but do not prescribe this project's finite saturation value. [CITED: https://arxiv.org/html/2104.00304] The bound must be selected by Wave 0 differential tests and must not inherit binary `25.0` without evidence. [ASSUMED]

Keep two prior forms: a sampler distribution may include exact zeros for deterministic fixtures, while a decoder prior must either be strictly positive or pass through an explicitly recorded smoothing policy before taking LLRs. The LLR definition is a log ratio in the real domain, while the current binary helper rejects probabilities at zero and one. [CITED: https://arxiv.org/html/2104.00304] [VERIFIED: src/bp_registry/canonical/numerics.py:65-86]

## Joint Pauli Sampling Contract

### Channel schema

Represent a memoryless joint Pauli channel as a validated `(n,4)` array in the declared `I,X,Y,Z` order. Require finite, nonnegative rows with sums equal to one within a named manifest tolerance; reject malformed rows instead of silently normalizing user input. This is the recommended strict contract needed to verify QBP-02. [ASSUMED]

Sample exactly one categorical value per qubit and derive its `(x,z)` truth pair from that value. Do not draw X and Z independently. The primary algorithms accept per-qubit four-state priors, and the current independent sampler uses two random draws that cannot express an arbitrary joint table. [CITED: https://arxiv.org/html/2104.00304] [VERIFIED: src/bp_registry/sampling.py:76-118]

Provide a named depolarizing constructor with the source formula `P(I)=1-p` and `P(X)=P(Y)=P(Z)=p/3`. [CITED: https://arxiv.org/html/2002.06502] Record both the named physical error rate and the resolved four probabilities in manifests and ledgers. [VERIFIED: .planning/PROJECT.md:64-80]

For any declared row `(p_I,p_X,p_Y,p_Z)`, verify analytically:

- `P(x=1)=p_X+p_Y`; [CITED: https://arxiv.org/html/2312.10950v2]
- `P(z=1)=p_Z+p_Y`; [CITED: https://arxiv.org/html/2312.10950v2]
- `P(x=1,z=1)=p_Y`; [CITED: https://arxiv.org/html/2312.10950v2]
- `Cov(x,z)=p_Y-(p_X+p_Y)(p_Z+p_Y)`. [ASSUMED]

The covariance identity is an algebraic test recommendation derived from the cited Pauli-to-bit mapping. [ASSUMED]

### Required fixtures

1. Deterministic all-I, all-X, all-Y, and all-Z channels verify categorical mapping, syndrome order, and exact zero/one sampling without statistical tolerance. [ASSUMED]
2. A single-Y fixture must flip every adjacent X-type and Z-type CSS check because Y has both symplectic components. [CITED: https://arxiv.org/html/2312.10950v2]
3. A non-product four-state prior with `p_Y != (p_X+p_Y)(p_Z+p_Y)` must prove the sampler preserves X/Z correlation and that separate marginal sampling does not reproduce the same `p_Y`. [ASSUMED]
4. The source `[[5,1,3]]` check matrix with error `IIIYI` at depolarizing rate `0.1` must be retained as a schedule-sensitive kernel regression: Kuo and Lai report parallel BP4 oscillation and serial BP4 convergence for this case. [CITED: https://arxiv.org/html/2002.06502]
5. Exact enumeration on at least one tiny tree must compare posterior four-state marginals, not only hard decisions. [ASSUMED]

## Independent Evaluation Contract

The evaluator receives the immutable original Pauli check problem, hidden Pauli truth, and candidate only after decoding. This keeps the current truth boundary: `HiddenTruth` is documented as “never native decoding,” and `ShotSample` exposes decoder input as `observation`. [VERIFIED: src/bp_registry/sampling.py:24-40,84-90]

Evaluate in this order:

1. Recompute candidate syndrome using an evaluator-owned symplectic routine and compare it with the immutable observed syndrome. A mismatch is `invalid_syndrome`. [CITED: https://arxiv.org/html/2312.10950v2] [VERIFIED: src/bp_registry/evaluator.py:61-66]
2. Multiply truth and recovery modulo Pauli phase, which is XOR in symplectic bits. Identity residual is `exact`. [CITED: https://arxiv.org/html/2312.10950v2] [VERIFIED: src/bp_registry/evaluator.py:67-69]
3. Test residual membership in the stabilizer row space. A nonidentity stabilizer residual is `stabilizer_equivalent`. [CITED: https://arxiv.org/html/2312.10950v2] [VERIFIED: src/bp_registry/evaluator.py:70-76]
4. Independently compute residual action on the declared logical basis. A syndrome-valid residual with nontrivial logical action is `logical_failure`; row-space and logical-action checks must agree when the basis is present. [CITED: https://arxiv.org/html/2312.10950v2] [VERIFIED: src/bp_registry/evaluator.py:77-83]

Recommend a general Pauli stabilizer/logical model with a lossless CSS compiler so the non-CSS five-qubit source fixture can be evaluated end to end. This broadens the data model beyond the minimum CSS experiments but matches the baseline kernel's source domain. [ASSUMED]

Independence requires separate evaluator algebra or exhaustive reference code; importing the kernel's commutation lookup into the evaluator would allow one wrong table to validate itself. [ASSUMED]

## Policy Compatibility Matrix

The Phase 10 registry should be closed and fail during preflight, before sampling. The repository's existing compatibility architecture already requires resolution before a run and rejects policies with incompatible state ownership. [VERIFIED: .planning/research/ARCHITECTURE.md:53-57,63-73]

| Policy | Phase 10 disposition | Source basis / reason |
|--------|----------------------|-----------------------|
| Scalar LLR sum-product + flooding | **Admit: source-backed baseline** | Lai and Kuo Algorithm 1 specifies parallel LLR-BP with scalar edge messages and three-component node beliefs. [CITED: https://arxiv.org/html/2104.00304] |
| Variable-node serial BP4 | **Admit: source-backed** | Kuo and Lai specify serial BP4 and report the `IIIYI` convergence contrast. [CITED: https://arxiv.org/html/2002.06502] |
| Check-message normalization | **Admit: source-backed** | Divide `Δ_{m→n}` by declared `α_c>0` before subsequent computations. [CITED: https://arxiv.org/html/2104.00304] |
| Check-message offset | **Admit: source-backed** | Apply `sign(Δ) max(0, |Δ|-β)` for declared `β>0`. [CITED: https://arxiv.org/html/2104.00304] |
| Q-BPGD | **Admit: required, source-backed intervention** | Yao Algorithm 3 defines reliability, fixation, round count, and early success for quaternary BP. [CITED: https://arxiv.org/html/2312.10950v2] |
| MBP4 | **Compatible source profile; plan after baseline/Q-BPGD or explicitly defer** | Kuo and Lai define a distinct quaternary LLR recurrence with `1/α` posterior scaling and fixed edge inhibition. It is not the binary Phase 4 memory transform. [CITED: https://arxiv.org/html/2104.13659] |
| AMBP4 | **Do not include without its complete adaptive search contract** | The MBP paper treats adaptive MBP as a separate algorithm; a scalar `α` field alone is incomplete. [CITED: https://arxiv.org/html/2104.13659] |
| Binary SPA | **Reject in quaternary registry** | It factorizes X and Z and cannot represent one joint Y variable/prior. [VERIFIED: .planning/research/ARCHITECTURE.md:37-43] |
| Binary min-sum / normalized min-sum / offset min-sum | **Reject unless a quaternary derivation is added and labeled adaptation** | Existing registered rules are binary, while the source-backed quaternary offset/normalization acts on scalar commutation C2V messages. [VERIFIED: src/bp_registry/canonical/contracts.py:62-67] [CITED: https://arxiv.org/html/2104.00304] |
| Binary damping, field mixing, momentum, EWA, Relay memory | **Reject automatic port; source-qualify individually** | The current audit explicitly labels these executions as binary CSS adaptations, including the GF(4)-source momentum reduced to scalar binary LLR. [VERIFIED: docs/memory-policy-sources.md:1-17,37-72] |
| Residual, randomized, group-shuffled, layered schedules | **Reject until quaternary atomicity/freshness/residual semantics are derived** | Their names exist in the binary registry, but no Phase 10 source derivation was established in this research. [VERIFIED: src/bp_registry/canonical/contracts.py:64-67] [ASSUMED] |
| OSD/LSD/SI/OTF postprocessing | **Out of Phase 10 execution scope** | Phase 7 optional postprocessing remains paused and project priority keeps BP-internal modifications first. [VERIFIED: .planning/STATE.md:4-11,27-38; AGENTS.md:14,49] |

### Q-BPGD Contract

Implement Algorithm 3 as a persistent Q-BP session with controller-owned decimation state:

1. Initialize every qubit with `(1-p,p/3,p/3,p/3)` for the source depolarizing profile; accept general declared joint priors only under a separately labeled canonical extension. [CITED: https://arxiv.org/html/2312.10950v2]
2. Maintain the undecimated set `V_u`; run exactly `T` Q-BP iterations in each of at most `n` rounds; form a hard Pauli candidate and return early if it matches the original syndrome. [CITED: https://arxiv.org/html/2312.10950v2]
3. Define reliability as the maximum of the four normalized posterior components; choose the maximum-reliability undecimated variable and its maximum-probability Pauli value. [CITED: https://arxiv.org/html/2312.10950v2]
4. Replace that variable's channel weights with the source-literal vector containing `1-ε` at the selected Pauli and `ε` at each other Pauli; remove the variable from `V_u`. The simulation source states `ε=1×10^-10`. [CITED: https://arxiv.org/html/2312.10950v2]
5. Continue the existing committed BP state across rounds unless a future author implementation establishes different state semantics; record this as a canonical interpretation because the paper pseudocode says “run Q-BP” but does not resolve all buffer-reset details. [ASSUMED]

The literal fixation vector sums to `1+2ε`, so its ratios are defined but it is not a normalized probability vector. Preserve the raw source weights, normalize them for a probability API by their common sum, and record both forms; changing the leading term to `1-3ε` would be an unmarked algorithm edit. [CITED: https://arxiv.org/html/2312.10950v2] The normalize-for-API choice is an interpretation that must be locked in the manifest. [ASSUMED]

The source writes `argmax` without a tie rule. Use a persisted deterministic ordering for canonical replay, tentatively lowest qubit index and `I<X<Y<Z`, and label it an interpretation. [ASSUMED]

### MBP4 boundary

MBP4 is mathematically compatible with the same Pauli checks and LLR quantizer, but it changes the variable recurrence: the posterior anticommute sum is scaled by `1/α`, while the outgoing-edge inhibition `-<W,S_mn>Δ_m→n` remains unscaled. [CITED: https://arxiv.org/html/2104.13659] This is a distinct update/state-memory policy and must not be implemented by applying the Phase 4 binary memory adapter after ordinary Q-BP. [VERIFIED: docs/memory-policy-sources.md:1-24] [CITED: https://arxiv.org/html/2104.13659]

Phase 10 can satisfy QBP-04 with flooding, serial, normalization/offset, and Q-BPGD. Implement MBP4 only if the plan has capacity after the baseline, sampler, evaluator, and required Q-BPGD gates; otherwise preserve it as the next source-qualified quaternary policy. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```mermaid
flowchart TD
    A[Typed Pauli code + joint channel manifest] --> B{Preflight}
    B -->|invalid algebra/prior/composition| X[Reject before sampling]
    B -->|valid| C[Compile immutable Pauli problem + typed edge table]
    C --> D[Sample one I/X/Y/Z value per qubit]
    D --> E[Decoder-visible full syndrome]
    D --> F[Hidden Pauli truth]
    E --> G[Scalar LLR-BP4 session]
    G --> H{Policy controller}
    H -->|flooding/serial/normalization| G
    H -->|Q-BPGD fixation| G
    G --> I[Pauli candidate + four-state marginals + work/events]
    I --> J[Independent original-problem evaluator]
    F --> J
    J --> K[Outcome + logical action]
    I --> L[Versioned ledger / trace]
    K --> L
    M[Vector BP4 + exact enumeration test oracles] -. differential validation .-> G
```

This flow follows the project's required compile/sample/decode/evaluate lifecycle and keeps truth outside the policy controller. [VERIFIED: .planning/research/ARCHITECTURE.md:63-73]

### Recommended Project Structure

```text
src/bp_registry/
├── pauli.py                         # typed Pauli/symplectic algebra shared with evaluator
├── quaternary_sampling.py           # categorical joint channel and Pauli shot
├── quaternary_evaluator.py          # independent syndrome/equivalence/logical checks
└── canonical/quaternary/
    ├── problems.py                  # immutable checks, priors, candidates, semantic hashes
    ├── numerics.py                  # three-LLR profile, quantization, stable box-plus
    ├── kernel.py                    # scalar LLR-BP4 pure updates/session
    ├── schedules.py                 # admitted flooding and serial semantics
    ├── guided_decimation.py         # source-profile Q-BPGD controller
    ├── compatibility.py             # closed policy registry/preflight
    ├── contracts.py                 # strict manifests and resolved evidence
    └── execution.py                 # sampling boundary, ledger, replay
tests/canonical/quaternary/
├── test_algebra.py
├── test_sampling.py
├── test_vector_oracle.py
├── test_kernel.py
├── test_schedules.py
├── test_bpgd.py
├── test_evaluator.py
└── test_public_execution.py
```

The package boundary is a recommendation that makes the second mathematical kernel explicit; exact filenames are not locked by upstream context. [ASSUMED]

### Pattern 1: Immutable original problem and derived session state

**What:** Hash ordered Pauli checks, full ordered syndrome, logical basis, prior order, and numerical profile into the immutable original problem. Keep edge messages, marginals, decimation eligibility, and round/iteration counters in a session owned by one attempt. [VERIFIED: .planning/research/ARCHITECTURE.md:63-72]

**When to use:** Every canonical Q-BP or Q-BPGD shot. [VERIFIED: .planning/ROADMAP.md:523-537]

### Pattern 2: Kernel emits marginals; controllers consume them

**What:** The kernel exposes normalized four-state posterior marginals as a typed output without allowing interventions to inspect hidden truth. Q-BPGD consumes reliability and changes only the declared channel prior/eligibility state. [CITED: https://arxiv.org/html/2312.10950v2]

**When to use:** Any intervention whose source ranks or fixes Pauli variables. [CITED: https://arxiv.org/html/2312.10950v2]

### Pattern 3: Source profile versus controlled extension

**What:** Keep `yao-qbpgd-depolarizing-v2` source settings separate from a general-prior Q-BPGD extension. Both may share code, but manifests must persist fidelity label, raw source settings, resolved priors, interpretations, and source revision. [VERIFIED: AGENTS.md:17-18,64]

**When to use:** Whenever a paper's policy is executed outside its exact noise, code, schedule, or reset semantics. [VERIFIED: .planning/PROJECT.md:82-89]

### Anti-Patterns to Avoid

- **Two independent binary decoders presented as Q-BP:** this loses the joint Y state and is only a comparison arm. [VERIFIED: .planning/research/ARCHITECTURE.md:37-43]
- **One widened binary data class:** it hides the full-syndrome and typed-edge change inside binary field names. [VERIFIED: src/bp_registry/canonical/problems.py:20-98]
- **Policy names as compatibility proof:** a binary `normalized_min_sum` and a quaternary normalized commutation message are different equations. [VERIFIED: .planning/research/ARCHITECTURE.md:77-88]
- **Shared algebra between kernel and evaluator:** one error could self-validate. [ASSUMED]
- **Reproduction settings hidden as defaults:** source and controlled configurations answer different questions. [VERIFIED: AGENTS.md:16-18]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stable log-sum | Direct `log(exp(a)+exp(b))` | `numpy.logaddexp` / ordered reduction | Official NumPy support avoids overflow/underflow in log probability sums. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html] |
| Check parity convolution | General GF(4) multiplication tables or FFT | Binary commute/anticommute quantization plus box-plus | The source factor is binary commutation parity and admits scalar messages. [CITED: https://arxiv.org/html/2104.00304] |
| Scientific outcome labels | Decoder-local success flags | Existing four outcome meanings plus independent logical checks | The existing evaluator already distinguishes syndrome, exact, stabilizer, and logical outcomes. [VERIFIED: src/bp_registry/evaluator.py:13-83] |
| Replay identity | Ad hoc random seeds inside policies | Existing manifest identity + shot ID pattern and decoder-local substreams | Current sampling hashes manifest identity and shot ID; project architecture separates physical and decoder randomness. [VERIFIED: src/bp_registry/sampling.py:60-73,84-90] |
| Q-BPGD reliability | Binary absolute LLR | Maximum normalized I/X/Y/Z posterior | This is the source definition for Q-BPGD. [CITED: https://arxiv.org/html/2312.10950v2] |
| Tiny-problem truth oracle | Another rearrangement of the production scalar equations | Exhaustive enumeration and conventional vector BP4 | These fail differently and can expose commutation or normalization errors. [CITED: https://arxiv.org/html/2002.06502] [ASSUMED] |

**Key insight:** the difficult part is preserving semantic independence among the joint channel, Pauli factor graph, source policy, and evaluator. Reusing equations without those boundaries would make an implementation fast to write but scientifically unauditable. [VERIFIED: AGENTS.md:59-64]

## Common Pitfalls

### Pitfall 1: Sampling X and Z separately

**What goes wrong:** The measured Y frequency becomes the product of marginal X and Z rates rather than the declared `p_Y`. [ASSUMED]

**Why it happens:** The current sampler draws two binary arrays independently. [VERIFIED: src/bp_registry/sampling.py:96-104]

**How to avoid:** Make one categorical draw in `I/X/Y/Z` and derive both symplectic bits. [CITED: https://arxiv.org/html/2312.10950v2]

**Warning signs:** Empirical `P(Y)` agrees with `P(x=1)P(z=1)` even for a deliberately correlated fixture. [ASSUMED]

### Pitfall 2: CSS row/syndrome order drift

**What goes wrong:** Correct Pauli candidates appear syndrome-invalid because X-check and Z-check rows were concatenated differently between compiler, sampler, manifest, and evaluator. [ASSUMED]

**Why it happens:** The existing public `ShotSample.observation` is the Z-check observation, while the mapping also stores both observations under string keys. [VERIFIED: src/bp_registry/sampling.py:105-118]

**How to avoid:** Persist row roles and combined order in semantic bytes and recompute them independently in tests. [ASSUMED]

**Warning signs:** X-only and Z-only fixtures pass separately while a Y fixture swaps syndrome segments. [ASSUMED]

### Pitfall 3: Losing correlations in a scalar-message implementation

**What goes wrong:** A developer stores only one scalar belief per qubit, confusing scalar edge messages with scalar node state, and cannot reconstruct four-state marginals for Q-BPGD. [ASSUMED]

**Why it happens:** The paper's efficiency result concerns edge messages; node beliefs remain a three-component LLR vector for nonidentity values. [CITED: https://arxiv.org/html/2104.00304]

**How to avoid:** Type edge commutation LLRs separately from node Pauli LLR vectors and normalized four-state marginals. [CITED: https://arxiv.org/html/2104.00304]

**Warning signs:** The kernel cannot return all four posterior probabilities required by Yao's reliability definition. [CITED: https://arxiv.org/html/2312.10950v2]

### Pitfall 4: Naive probability products and hyperbolic functions

**What goes wrong:** Messages underflow, `atanh` saturates, or zero inputs lead to unstable division. [CITED: https://arxiv.org/html/2104.00304]

**Why it happens:** The source equations are compact mathematical forms, while finite `float64` needs stable Jacobian-log/box-plus implementations. [CITED: https://arxiv.org/html/2104.00304]

**How to avoid:** Use the stable existing pairwise box-plus shape, a quaternary profile, ordered reduction, and log-sum-exp; reject nonfinite values with terminal evidence. [VERIFIED: src/bp_registry/canonical/numerics.py:52-62,95-138]

**Warning signs:** Tree-oracle differences grow with check degree or depend on edge iteration order. [ASSUMED]

### Pitfall 5: Silently “fixing” Q-BPGD source weights

**What goes wrong:** Replacing source `(1-ε,ε,ε,ε)` with `(1-3ε,ε,ε,ε)` changes the documented algorithm while still looking reasonable. [CITED: https://arxiv.org/html/2312.10950v2]

**Why it happens:** The source vector is used as a channel message and is not exactly normalized as printed. [CITED: https://arxiv.org/html/2312.10950v2]

**How to avoid:** Preserve the raw weights, normalize only by a common factor at the probability boundary, and ledger the interpretation. [ASSUMED]

**Warning signs:** The manifest contains only a normalized vector and cannot reconstruct the paper's literal inputs. [ASSUMED]

### Pitfall 6: Treating convergence as logical success

**What goes wrong:** A syndrome-valid candidate is counted as a successful recovery even when its residual is a nontrivial logical operator. [CITED: https://arxiv.org/html/2312.10950v2]

**Why it happens:** BP stopping checks the syndrome, while outcome classification needs hidden truth and logical operators. [VERIFIED: src/bp_registry/evaluator.py:61-83]

**How to avoid:** Record kernel convergence and final evaluator outcome as separate fields. [VERIFIED: AGENTS.md:60-63]

**Warning signs:** Every converged shot is reported as logical success. [ASSUMED]

### Pitfall 7: Porting binary policies by shared names

**What goes wrong:** Binary min-sum, damping, residual scheduling, or prior memory is applied to quaternary state without a derived operand, update order, reset rule, or source qualification. [VERIFIED: docs/memory-policy-sources.md:1-24]

**Why it happens:** The common lifecycle makes hooks look mechanically compatible even when the message algebra differs. [VERIFIED: .planning/research/ARCHITECTURE.md:77-88]

**How to avoid:** Use a quaternary capability registry with exact required/provided types and source labels. [ASSUMED]

**Warning signs:** A Phase 10 manifest accepts every current binary `kind` unchanged. [VERIFIED: src/bp_registry/canonical/contracts.py:62-73]

### Pitfall 8: Non-independent validation

**What goes wrong:** The same Pauli enum table or syndrome routine is imported by kernel, sampler, and evaluator, so a consistent mapping bug passes all tests. [ASSUMED]

**Why it happens:** Sharing a helper reduces code duplication but also removes fault independence. [ASSUMED]

**How to avoid:** Use independent symplectic evaluator code, hand fixtures, vector BP4, and exhaustive enumeration. [ASSUMED]

**Warning signs:** All algebra tests are round trips through one common function. [ASSUMED]

## Code Examples

The examples below are implementation skeletons derived from the cited equations; names and final module locations remain planner decisions. [ASSUMED]

### Explicit Pauli order and independent commutation

Source order quoted above: “0,1,2,3 representing the absence of error, or the presence of a Pauli σx, σy or σz error.” [CITED: https://arxiv.org/html/2312.10950v2]

```python
from enum import IntEnum

class Pauli(IntEnum):
    I = 0
    X = 1
    Y = 2
    Z = 3

SYMPLECTIC = {
    Pauli.I: (0, 0),
    Pauli.X: (1, 0),
    Pauli.Y: (1, 1),
    Pauli.Z: (0, 1),
}

def anticommutes(left: Pauli, right: Pauli) -> int:
    left_x, left_z = SYMPLECTIC[left]
    right_x, right_z = SYMPLECTIC[right]
    return (left_x * right_z + left_z * right_x) & 1
```

The bit mapping follows `Y=iXZ` and the symplectic product in Yao et al. [CITED: https://arxiv.org/html/2312.10950v2]

### Stable commutation quantization from three LLRs

```python
import numpy as np

def logsumexp(values: np.ndarray) -> float:
    return float(np.logaddexp.reduce(values))

def commutation_llr(pauli_log_weights: np.ndarray, edge_label: Pauli) -> float:
    # pauli_log_weights has declared order I, X, Y, Z.
    parity = np.array([anticommutes(Pauli(index), edge_label) for index in range(4)])
    return logsumexp(pauli_log_weights[parity == 0]) - logsumexp(
        pauli_log_weights[parity == 1]
    )
```

This implements the paper's ratio of total commuting probability to total anticommuting probability, using the official NumPy log-sum primitive. [CITED: https://arxiv.org/html/2104.00304] [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]

### Q-BPGD source-weight resolution

The source states `ε=1×10^-10` and places `1-ε` on the selected component and `ε` on each other component. [CITED: https://arxiv.org/html/2312.10950v2]

```python
SOURCE_EPSILON = 1e-10

def resolved_fixation(selected: Pauli) -> tuple[np.ndarray, np.ndarray]:
    raw = np.full(4, SOURCE_EPSILON, dtype=np.float64)
    raw[int(selected)] = 1.0 - SOURCE_EPSILON
    normalized = raw / raw.sum()
    return raw, normalized
```

Returning both arrays preserves the literal source weights and the normalization interpretation. [ASSUMED]

## State of the Art

| Old approach | Current recommended approach | When changed | Impact |
|--------------|------------------------------|--------------|--------|
| Conventional four-component edge messages | Refined scalar commute/anticommute messages with four-state node beliefs | Kuo–Lai arXiv:2002.06502v2, 2020 | Same reported BP4 output with lower check-node complexity. [CITED: https://arxiv.org/html/2002.06502] |
| Linear-domain scalar difference messages | Identity-referenced LLR vectors plus scalar box-plus edge messages | Lai–Kuo arXiv:2104.00304v3, 2021 | Stable log-domain implementation and direct normalization/offset policies. [CITED: https://arxiv.org/html/2104.00304] |
| Plain BP4 on short-cycle graphs | Serial/normalized BP4 and MBP4 as source-distinct policies | 2020–2023 source revisions | Schedule and recurrence are explicit policy dimensions, not generic tuning flags. [CITED: https://arxiv.org/html/2002.06502] [CITED: https://arxiv.org/html/2104.13659] |
| Binary-only guided decimation | Q-BPGD based on four-state posterior reliability and Pauli fixation | Yao et al. arXiv:2312.10950v2, 2024 | The intervention now consumes joint Pauli marginals and preserves Y as one value. [CITED: https://arxiv.org/html/2312.10950v2] |

**Deprecated/outdated for this phase:**

- Separate X/Z binary decoding is a controlled comparator, not the canonical correlated kernel. [VERIFIED: .planning/research/ARCHITECTURE.md:37-43]
- Conventional vector BP4 should not be the production engine; retain it as an independent oracle. [CITED: https://arxiv.org/html/2002.06502]
- The zero-disturbance all-neighbor boxminus optimization is unsuitable for the correctness baseline because the source marks it potentially approximate. [CITED: https://arxiv.org/html/2104.00304]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Keep existing work-vector fields and qualify their units rather than add arithmetic counters. | Current Repository Baseline | Work comparisons could miss a required schema distinction. |
| A2 | Persist Pauli label in each quaternary edge-table hash. | Canonical Mathematical Contract | Artifact identity could be insufficient if omitted. |
| A3 | Lock a combined CSS syndrome row order during Phase 10 planning. | Canonical Mathematical Contract | Cross-component syndrome evidence could drift. |
| A4 | Select quaternary saturation through Wave 0 differential tests rather than inherit `25.0`. | Numerical Contract | Numerical behavior and source comparisons depend on the bound. |
| A5 | Strict user priors must already sum to one; only explicitly source-literal weights may be normalized with raw values retained. | Sampling / Q-BPGD | A different API policy changes rejection and provenance semantics. |
| A6 | Include a general Pauli stabilizer/logical model, with CSS as a compiled subset. | Independent Evaluation | CSS-only scope would need a different five-qubit validation path. |
| A7 | Continue committed Q-BP messages across Q-BPGD rounds. | Q-BPGD Contract | The paper does not fully resolve buffer reset behavior; trajectories may differ. |
| A8 | Normalize Yao's literal fixation weights by their common sum for the probability API. | Q-BPGD Contract | This is source-ratio preserving but remains an interpretation. |
| A9 | Use lowest qubit ID and Pauli order `I<X<Y<Z` for unresolved ties. | Q-BPGD / hard decision | A different tie rule changes deterministic trajectories. |
| A10 | MBP4 may be deferred after required baseline and Q-BPGD without failing QBP-04. | Policy Compatibility | The planner may interpret “compositions” as requiring MBP4 now. |
| A11 | Use the proposed `canonical/quaternary/` module layout. | Architecture Patterns | Repository maintainers may prefer the current flat module convention. |
| A12 | The author implementation identity for Yao Q-BPGD remains unresolved; the current project record must not be read as proof of absence. | Open Questions | Reproduction planning could miss an available source implementation. |

## Open Questions

1. **Does Phase 10 lock general stabilizer support or CSS-only public execution?**
   - What we know: the source BP4 equations and the strongest Y fixture are general stabilizer equations, while Yao's published Q-BPGD section and the project's next experiment targets are CSS. [CITED: https://arxiv.org/html/2002.06502] [CITED: https://arxiv.org/html/2312.10950v2]
   - What's unclear: no Phase 10 `CONTEXT.md` chooses the public model boundary. [VERIFIED: gsd init.phase-op 10 on 2026-10-06]
   - Recommendation: implement a general Pauli check model and CSS compiler so the kernel is not artificially restricted; permit the planner to split non-CSS logical evaluation into a later task if scope pressure appears. [ASSUMED]

2. **What is the exact persisted combined syndrome order for compiled CSS artifacts?**
   - What we know: current code separately identifies Z checks and X checks, and the source formulas use one ordered stabilizer matrix. [VERIFIED: src/bp_registry/sampling.py:105-114] [CITED: https://arxiv.org/html/2312.10950v2]
   - What's unclear: no current quaternary artifact schema exists. [VERIFIED: repository file audit 2026-10-06]
   - Recommendation: lock row order and roles in semantic bytes before kernel work. [ASSUMED]

3. **What finite saturation and boundary behavior define the canonical quaternary numerical profile?**
   - What we know: current binary saturation is `25.0`; source Q-BP specifies real LLRs and stable log operations but not this project's finite bound. [VERIFIED: src/bp_registry/canonical/numerics.py:15-41] [CITED: https://arxiv.org/html/2104.00304]
   - What's unclear: the smallest bound that preserves oracle agreement over intended priors and degrees. [ASSUMED]
   - Recommendation: parameterize it, sweep adversarial tiny-tree fixtures, and freeze the selected profile before public manifests. [ASSUMED]

4. **How exactly are Q-BPGD buffers treated between rounds, and how are ties resolved?**
   - What we know: Algorithm 3 says to run Q-BP for `T` iterations, then decimate using maximum marginal reliability. [CITED: https://arxiv.org/html/2312.10950v2]
   - What's unclear: author-code identity, message reset/continuation, equal-reliability ties, and equal-component ties remain unresolved; the existing project record calls the author implementation identity unverified rather than absent. [VERIFIED: literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md:3-8,27-33]
   - Recommendation: persist the chosen interpretation, add sensitivity fixtures, and update it only if an authoritative implementation resolves the ambiguity. [ASSUMED]

5. **Should MBP4 be implemented in this phase?**
   - What we know: MBP4 has a source-defined compatible recurrence, while Q-BPGD is explicitly required. [CITED: https://arxiv.org/html/2104.13659] [VERIFIED: .planning/REQUIREMENTS.md:139]
   - What's unclear: plan capacity after the new model, sampler, evaluator, kernel, ledger, and Q-BPGD path. [ASSUMED]
   - Recommendation: treat MBP4 as the first stretch plan, never as a substitute for Q-BPGD. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Canonical runtime/tests | ✓ | `3.12.2` | — [VERIFIED: environment probe 2026-10-06] |
| NumPy | Kernel/sampler/oracles | ✓ | `2.2.6` | — [VERIFIED: environment probe 2026-10-06] |
| SciPy | Existing scientific stack | ✓ | `1.17.1` | NumPy/GF(2) helpers for Phase 10 core [VERIFIED: environment probe 2026-10-06] |
| Pydantic | Strict manifests | ✓ | `2.13.5` | — [VERIFIED: environment probe 2026-10-06] |
| pytest | Validation | ✓ | `9.0.3` | — [VERIFIED: environment probe 2026-10-06] |
| Kuo C reference | Optional native differential/reference work | Source available | commit `402a83e…` | Paper equations + canonical/vector oracles [CITED: https://github.com/kywukuo/qLDPC_dec/tree/402a83e8afd0df5203693aeeed1e42f1900e344d] |
| Yao Q-BPGD author code | Source reproduction identity | Unresolved | — | Implement paper Algorithm 3 and label interpretations [VERIFIED: literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md:3-8] [ASSUMED] |

**Missing dependencies with no fallback:** None for canonical Phase 10 execution. [VERIFIED: environment probe and Standard Stack recommendation 2026-10-06]

**Missing dependencies with fallback:** The unresolved Yao author implementation identity does not block a paper-equation canonical realization, but it blocks any claim of author-code trajectory agreement. [VERIFIED: literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md:3-8]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `9.0.3` [VERIFIED: environment probe 2026-10-06] |
| Config file | `pyproject.toml`, verbatim `testpaths = ["tests"]` and `pythonpath = ["src"]` [VERIFIED: pyproject.toml:28-30] |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` [ASSUMED] |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` [VERIFIED: .planning/config.json workflow.test_command, read 2026-10-06] |

The existing targeted baseline `tests/canonical/test_numerics.py tests/test_sampling.py tests/test_css_small.py tests/test_phase6_public_execution.py` passed `24` tests in `1.28s` on 2026-10-06. [VERIFIED: pytest probe 2026-10-06]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QBP-01 | Pauli commutation, scalar LLR messages, vector/exact oracle agreement, numerics | unit + differential | `pytest -q tests/canonical/quaternary/test_algebra.py tests/canonical/quaternary/test_vector_oracle.py tests/canonical/quaternary/test_kernel.py -x` | ❌ Wave 0 [VERIFIED: repository file audit 2026-10-06] |
| QBP-02 | Strict joint priors, one categorical Pauli draw, Y and correlation fixtures | unit + property | `pytest -q tests/canonical/quaternary/test_sampling.py -x` | ❌ Wave 0 [VERIFIED: repository file audit 2026-10-06] |
| QBP-03 | Independent syndrome/exact/stabilizer/logical outcomes | unit + exhaustive | `pytest -q tests/canonical/quaternary/test_evaluator.py -x` | ❌ Wave 0 [VERIFIED: repository file audit 2026-10-06] |
| QBP-04 | Closed compatibility, Q-BPGD semantics, trace/replay and unsupported-policy rejection | unit + integration | `pytest -q tests/canonical/quaternary/test_bpgd.py tests/canonical/quaternary/test_public_execution.py -x` | ❌ Wave 0 [VERIFIED: repository file audit 2026-10-06] |

### Required Oracle Ladder

1. **Hand algebra:** full 4×4 commutation table and every single-Pauli syndrome. [CITED: https://arxiv.org/html/2002.06502]
2. **Exact enumeration:** enumerate every Pauli assignment on tiny problems, condition on syndrome, and compute normalized posterior marginals. [ASSUMED]
3. **Conventional vector BP4:** compare each iteration/message/marginal with scalar LLR-BP4 on trees. [CITED: https://arxiv.org/html/2002.06502]
4. **Source fixtures:** five-qubit `IIIYI`, depolarizing prior, Q-BPGD fixation/reliability, and MBP4 recurrence if implemented. [CITED: https://arxiv.org/html/2002.06502] [CITED: https://arxiv.org/html/2312.10950v2] [CITED: https://arxiv.org/html/2104.13659]
5. **Public evidence:** manifest round trip, semantic hashes, truth-boundary tests, work reconstruction, trace truncation, replay, and tamper rejection. [VERIFIED: .planning/research/ARCHITECTURE.md:63-73]

### Sampling Rate

- **Per task commit:** run the new file-specific test command plus the closest existing boundary test. [ASSUMED]
- **Per wave merge:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary tests/test_sampling.py tests/test_css_small.py tests/test_phase6_public_execution.py`. [ASSUMED]
- **Phase gate:** full suite green before `$gsd-verify-work`. [VERIFIED: .planning/config.json workflow.test_command and GSD workflow]

### Wave 0 Gaps

- [ ] `tests/canonical/quaternary/test_algebra.py` — QBP-01 Pauli order, symplectic mapping, commutation table, CSS compiler and semantic hash. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_vector_oracle.py` — QBP-01 conventional BP4 and exact-enumeration oracles. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_kernel.py` — QBP-01 scalar update equations, saturation/nonfinite behavior, hard decisions and tree agreement. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_sampling.py` — QBP-02 prior validation, depolarizing mapping, deterministic I/X/Y/Z and non-product correlation. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_evaluator.py` — QBP-03 exhaustive outcome and CSS/general-Pauli agreement. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_schedules.py` — source flooding versus variable-serial freshness and `IIIYI`. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_bpgd.py` — QBP-04 reliability, undecimated selection, raw/resolved fixation, state continuation, early success, round cap, work and ties. [ASSUMED]
- [ ] `tests/canonical/quaternary/test_public_execution.py` — QBP-04 preflight, closed registry, manifests, ledger grammar, replay, tamper and truth boundary. [ASSUMED]
- [ ] Shared exact-enumeration fixtures and independent evaluator helpers under `tests/canonical/quaternary/conftest.py`. [ASSUMED]
- [ ] No framework install is needed. [VERIFIED: environment probe 2026-10-06]

## Security Domain

Security enforcement is enabled at ASVS level 1 in the project configuration. [VERIFIED: .planning/config.json workflow.security_enforcement and workflow.security_asvs_level, read 2026-10-06]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No authenticated service is introduced by this phase. [VERIFIED: .planning/ROADMAP.md:523-537] |
| V3 Session Management | no | Decoder sessions are in-process scientific state, not user authentication sessions. [VERIFIED: .planning/research/ARCHITECTURE.md:63-73] |
| V4 Access Control | no | No multi-user authorization boundary is added. [VERIFIED: .planning/ROADMAP.md:523-537] |
| V5 Input Validation | yes | Strict frozen Pydantic manifests; finite probability/LLR checks; exact shapes, enum values, and closed policy registries. [VERIFIED: src/bp_registry/canonical/contracts.py:12-18,76-99] |
| V6 Cryptography | yes, integrity only | Reuse project semantic/content SHA-256 for artifact and ledger identity; do not invent cryptography. [VERIFIED: src/bp_registry/css.py:128-147] |

### Known Threat Patterns for the Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| NaN/Inf or malformed probability rows alter decisions | Tampering | `allow_inf_nan=False`, explicit finite/range/sum checks, terminal numerical evidence. [VERIFIED: src/bp_registry/canonical/contracts.py:17-18; src/bp_registry/canonical/numerics.py:52-81] |
| Unknown manifest fields or policy kinds silently accepted | Tampering | `extra="forbid"` plus a quaternary closed compatibility registry. [VERIFIED: src/bp_registry/canonical/contracts.py:17-18,62-73] |
| Hidden truth leaks into Q-BPGD reliability or stopping | Information disclosure / scientific integrity | Separate observation and hidden truth types; pass only marginals/observations to policies. [VERIFIED: src/bp_registry/sampling.py:16-40] |
| Artifact or ledger substitution | Tampering | Semantic hashes, content hashes, and structural replay against the preflighted public identity. [VERIFIED: src/bp_registry/css.py:128-147; src/bp_registry/canonical/verification.py:1-31] |
| Unbounded rounds/traces cause resource exhaustion | Denial of service | Typed `T`, at most `n` Q-BPGD rounds, work caps, and bounded trace sidecars. [CITED: https://arxiv.org/html/2312.10950v2] [VERIFIED: src/bp_registry/canonical/budgets.py:18-65] |
| GPL reference code copied into canonical package | Legal/provenance risk | Keep the Kuo repository isolated and derive canonical code from cited equations and independent tests. [CITED: https://github.com/kywukuo/qLDPC_dec] |

## Sources

### Primary repository sources (HIGH confidence)

- `.planning/REQUIREMENTS.md:134-139` — QBP-01 through QBP-04. [VERIFIED: .planning/REQUIREMENTS.md:134-139]
- `.planning/ROADMAP.md:523-537` — Phase 10 goal, dependency, success criteria, research focus, and priority. [VERIFIED: .planning/ROADMAP.md:523-537]
- `.planning/research/ARCHITECTURE.md:35-88` — kernel-family boundary, joint Pauli semantics, lifecycle, ownership, and compatibility. [VERIFIED: .planning/research/ARCHITECTURE.md:35-88]
- `src/bp_registry/canonical/problems.py:20-98` — current binary problem and candidate limits. [VERIFIED: src/bp_registry/canonical/problems.py:20-98]
- `src/bp_registry/canonical/numerics.py:15-157` — current numerical profile and stable scalar primitives. [VERIFIED: src/bp_registry/canonical/numerics.py:15-157]
- `src/bp_registry/canonical/contracts.py:17-85` — strict manifests and current closed binary policy registry. [VERIFIED: src/bp_registry/canonical/contracts.py:17-85]
- `src/bp_registry/canonical/budgets.py:18-120` — current atomic work vector. [VERIFIED: src/bp_registry/canonical/budgets.py:18-120]
- `src/bp_registry/sampling.py:16-118` — truth boundary and current separate-X/Z sampler. [VERIFIED: src/bp_registry/sampling.py:16-118]
- `src/bp_registry/evaluator.py:13-83` — current outcome vocabulary and independent CSS evaluation. [VERIFIED: src/bp_registry/evaluator.py:13-83]
- `docs/memory-policy-sources.md:1-86` — existing memory source/adaptation labels. [VERIFIED: docs/memory-policy-sources.md:1-86]
- `literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md:3-37` — existing Yao source status and unresolved implementation identity. [VERIFIED: literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md:3-37]

### Primary mathematical and implementation sources (MEDIUM confidence by configured seam)

- [Yao et al., arXiv:2312.10950v2](https://arxiv.org/html/2312.10950v2) — Pauli/symplectic conventions, outcome meanings, Q-BPGD Algorithm 3, reliability, fixation, `ε`, and experiments. [CITED: https://arxiv.org/html/2312.10950v2]
- [Kuo and Lai, arXiv:2002.06502v2](https://arxiv.org/html/2002.06502) — conventional vector BP4, scalar delta-rule BP4, serial schedule, normalization, and five-qubit `IIIYI` fixture. [CITED: https://arxiv.org/html/2002.06502]
- [Lai and Kuo, arXiv:2104.00304v3](https://arxiv.org/html/2104.00304) — identity-referenced LLRs, commutation quantizer, scalar box-plus updates, stable numerical recommendations, schedules, normalization, and offset. [CITED: https://arxiv.org/html/2104.00304]
- [Kuo and Lai, arXiv:2104.13659v2](https://arxiv.org/html/2104.13659) — MBP4 recurrence, fixed inhibition, schedules, and adaptive boundary. [CITED: https://arxiv.org/html/2104.13659]
- [NumPy 2.2 `logaddexp`](https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html) — official stable log-sum primitive. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]
- [Kuo `qLDPC_dec` repository at commit `402a83e…`](https://github.com/kywukuo/qLDPC_dec/tree/402a83e8afd0df5203693aeeed1e42f1900e344d) — GPL C reference archive and its stated paper association. [CITED: https://github.com/kywukuo/qLDPC_dec/tree/402a83e8afd0df5203693aeeed1e42f1900e344d]

### Tertiary (LOW confidence / requires planning confirmation)

- Module layout, general-stabilizer public scope, finite saturation selection, Q-BPGD state continuation, source-weight normalization, and tie rules are the explicit assumptions A1–A12 above. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — existing pins, installed versions, and test command were probed; no new package is proposed. [VERIFIED: pyproject.toml:5-30; environment probe 2026-10-06]
- Mathematical kernel: MEDIUM — equations and equivalence claims come from primary paper versions retrieved through a seam classified MEDIUM. [CITED: https://arxiv.org/html/2104.00304]
- Architecture: HIGH for existing boundaries; MEDIUM for the proposed quaternary package/data model. [VERIFIED: .planning/research/ARCHITECTURE.md:35-88] [ASSUMED]
- Q-BPGD semantics: MEDIUM for paper-literal behavior; LOW for reset, normalization, and tie interpretations. [CITED: https://arxiv.org/html/2312.10950v2] [ASSUMED]
- Pitfalls and validation: MEDIUM overall — source facts are cited and project-specific oracle design is explicit as assumptions. [CITED: https://arxiv.org/html/2002.06502] [ASSUMED]

**Research date:** 2026-10-06  
**Valid until:** 2026-11-05 for implementation planning; recheck source-code identity and installed environment before reproduction planning. [ASSUMED]
