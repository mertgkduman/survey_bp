# Memory-policy source audit

This register binds the Phase 4 executable names to their operands, state, and
scientific qualification.  A source equation and a CSS execution are distinct
claims: every entry below that enters the scalar binary CSS engine is labelled
as an adaptation unless the source itself defines that regime.

## Selected equations

| Registered name | Primitive and equation | Target and advance boundary | Initialization and reset | Fidelity label |
| --- | --- | --- | --- | --- |
| `gy-pfister-v2c-damping-v1` | `v2c_out = (1-gamma) v2c_old + gamma v2c_fresh`, `gamma in [0, 1]` | V2C after a fresh V2C calculation; declared `local_update` or `source_iteration` | channel-prior V2C is the initial old vector; reset at an attempt or Relay leg | source equation; binary CSS component adaptation |
| `pretti-pdbp-field-mix-v1` | `h_out = (1-gamma) h_fresh + gamma h_old`, `gamma in [0, 1)` | belief/effective field after fresh C2V aggregation; declared `local_update` or `source_iteration` | channel field initializes the old field; commit stores the mixed field | classical source, binary CSS adaptation |
| `pretti-pdprime-delta-mix-v1` | `Delta = sum(c2v_fresh-c2v_old)` over edge-aligned C2V rows; `h_out = h_old + (1-gamma) Delta`, `gamma in [0, 1)` | belief/effective field after a matched old/fresh C2V pair; declared `local_update` or `source_iteration` | channel field and C2V matrix initialize history; commit stores both field and fresh C2V | classical source, binary CSS adaptation |
| `chen-posterior-momentum-v1` | `g_t = gamma*g_(t-1) + (1-gamma)*(Q_(t-1)-Q_fresh)`; `Q_t = Q_(t-1)-alpha*g_t` | posterior belief at the declared boundary; V2C uses `Q_t - original_current_c2v` | `g_0=0`, `Q_0=prior`; reset at an attempt or Relay leg | GF(4) source, scalar-LLR CSS adaptation |
| `ewa-prior-memory-v1` | `prior_t = alpha*prior_0 + (1-alpha)*posterior_(t-1)` | prior before the source iteration's BP updates | first posterior is `prior_0`; retained at attempt lifetime | source equation, binary CSS adaptation |
| `relay-affine-prior-memory-v1` | `bias_t = (1-gamma)*prior_0 + gamma*posterior_(t-1)` | prior/bias before the Relay source iteration's min-sum updates | initial posterior is the prior or transferred predecessor posterior; retained at leg lifetime | source equation, code-capacity CSS adaptation |

`src/bp_registry/canonical/memory.py` implements the first four mechanisms as
separate proposal and commit state machines.  Every proposal checks finite,
complete operands and its declared boundary; commit ownership prevents one
binding from replacing another binding's history.  PDBP's field mix and
PD-prime's C2V delta therefore cannot be selected merely by changing a
coefficient of one common implementation.

## Reparameterized affine memory

`EWAInitPriorMemory` and `RelayAffinePriorMemory` delegate to the same
`AffinePriorMemory` primitive.  For uniform parameters,
`gamma_relay = 1 - alpha_ewa`, so both source forms produce the same prior for
the same `prior_0` and previous posterior.  The aliases preserve their source
names, state lifetime, and fidelity labels; they do not claim that EWAInit and
Relay are distinct equations.  Disordered Relay gamma assignments, including
negative values, are an assignment/controller extension that is deliberately
outside this uniform primitive and is handled by the later composition work.

## Primary sources and selected variants

1. Gökduman, Yao, and Pfister, *Damped BPGD*,
   [arXiv:2411.08177](https://arxiv.org/abs/2411.08177): selected for V2C
   damping.  Its gamma weights the fresh V2C operand, which is verified by
   endpoint fixtures.
2. Pretti, *PDBP and PD-prime BP*,
   [arXiv:1407.0521](https://arxiv.org/abs/1407.0521): selected as two distinct
   classical mechanisms.  PDBP mixes full effective fields; PD-prime applies
   an edge-aligned C2V delta to the old field.  Both CSS uses are adaptations.
3. Chen et al., *Momentum-BP and EWAInit-BP*,
   [arXiv:2407.11523](https://arxiv.org/abs/2407.11523): selected for the
   velocity recurrence, `g0=0`, `Q0=prior`, original-C2V subtraction, and EWA
   prior update.  The project executes the momentum recurrence as a scalar LLR
   CSS adaptation rather than attributing GF(4) performance to CSS.
4. Müller et al., *Relay-BP*,
   [arXiv:2506.01779](https://arxiv.org/abs/2506.01779): selected for affine
   Relay memory and its leg-local lifetime.  Its circuit experiments are not
   represented as CSS reproduction claims.

Rejected as separate mechanisms: PDBP coefficient changes are configurations,
not a new rule; uniform EWAInit and uniform Relay memory are a
reparameterization, not two algorithms; the local experimental relay fork's
message-mix variants have no pinned primary publication and remain unresolved
interpretations rather than source-faithful policies.

## Reference-code availability and drift

| Source | Original code status | Drift or unresolved detail | Handling |
| --- | --- | --- | --- |
| gy-pfister | no original policy implementation pinned for this rule | source BPGD context differs from standalone CSS damping | retain source-equation component-adaptation label |
| pretti | no original implementation pinned | source is classical; graph/field translation is not a quantum claim | retain classical-source CSS-adaptation label and hand fixture |
| chen | no original implementation pinned | GF(4) posterior semantics differ from scalar binary LLR semantics | retain GF(4)-source scalar-LLR-adaptation label and test original-C2V subtraction |
| ewa | same Chen source; no original code pin | EWA's source iteration order must remain explicit in composition integration | retain source-equation CSS-adaptation label |
| relay | original `trmue/relay` v0.2.2, commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, is the reference | paper values, Rust defaults, Python constructor defaults, and README example differ; the local `mg551-duke/relay` fork is not source-equivalent | preserve source/version/configuration separately; treat canonical CSS as an adaptation and native instrumentation gaps as unavailable evidence |

The relay paper/code audit records these materially different values: the paper
uses source circuit settings, the Rust release defaults to `pre_iter=80`,
`num_sets=300`, `set_max_iter=60`, and interval `(-0.24, 0.66)`, while the
Python constructor and README expose other choices.  No one of these values is
silently substituted for another in a saved configuration.

## Fixture evidence

`tests/canonical/test_memory_policies.py` checks V2C endpoints, PDBP/PD-prime
divergence on independent field and C2V operands, exact momentum velocity and
original-C2V subtraction, reset behavior, and EWA/Relay equality under
`gamma=1-alpha`.  These tests establish algebra and policy semantics; they do
not establish a published curve reproduction.
