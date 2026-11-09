# Spike Conventions

Patterns established by presentation reproduction and canonical-kernel audit sessions.

## Stack

Use the project's Python, NumPy, SciPy, Numba, and Matplotlib environment for decoder feasibility and plots.

## Structure

Keep presentation source values, decoder policy files, local measurements, and plots together under the user-requested `from_dr_pfister_presentetations/` folder. Store GSD investigation trails under `.planning/spikes/`.

Kernel audit probes and their small deterministic evidence bundles live directly under their `.planning/spikes/NNN-*/` directories. The presentation-folder requirement belongs to presentation reproduction, not to unrelated spike ideas.

## Patterns

- Label every number as reported source data or local measured data.
- Use deterministic paired error streams, per-shot JSONL ledgers, seed and denominator fields, and ledger hashes.
- Verify CSS code parameters and stabilizer/logical outcome semantics before interpreting decoder rates.
- Mark unspecified source numerical choices as assumptions; never call an adaptation a source-faithful reproduction.
- Freeze candidate policies on screening seeds before measuring independent holdouts; retain unfavorable arms and inconclusive paired comparisons.
- Preserve the evidence identity and behavior of frozen numerical v1 profiles. Promote changed clipping, check safeguards, tie rules, or damping under a new profile ID, and replay selected held-out shots through production code.
- Validate algorithms against independent probability-domain or exact small-graph oracles; cross-backend agreement and curve proximity alone do not prove correctness.
- Keep native source/version/binary identity and correspondence scope explicit. An extracted native function probe is not a complete native decoder reproduction.
- Test identity policies, parameter sensitivity, initial candidates, budget-denial boundaries, and cumulative work independently of deterministic replay.
- Diagnostic probe exit success means the experiment ran. Publish failed invariant counts and counterexamples separately from passing regression-suite counts.

- Keep pre-fix audit evidence immutable. Record fixes in a new numbered spike with failing regression evidence, passing regression evidence, and a source-hashed post-fix qualification.

## Tools and libraries

The project `.venv` supplies the pinned versions in `pyproject.toml`; no new dependency was installed for this spike.

## Constructor and performance qualification

- Enforce compiled graph contracts in construction itself, including dataclass replacement; validate and own CSR buffers before bounds-unchecked native execution.
- Keep failed integration evidence, then rerun relevant regressions against the final source. Use a fresh Numba cache when changing shared compiled helpers.
- Compare CPU throughput on identical policy, input and stopping contracts; separate first-call/JIT costs from warm timing and retain matching shot ledgers.

- Audit admitted numerical controls across every accepting schedule/controller, and include initial-convergence and zero-iteration returns when checking state validation. Validate normalized execution-dtype state, not only pre-conversion input.

- Check controller-specific controls for a real execution operand before exposing them in sweeps or HTML. Distinct recorded configurations alone do not establish distinct implemented policies.
- Name the operand weighted by each memory coefficient in identity tests; V2C gamma weights the fresh message, whereas other gamma parameters can weight history. Preserve and explain incorrect probe assumptions separately from production findings.
- Carry prior hardware qualification only with matching source identities and explicit timing scope. Fresh CPU validation of stored GPU records is not a new hardware run; distinguish decode/transfer/result binding from JIT and JSON export costs.

- Record CPU affinity and physical-core topology with benchmarks. If an unchanged control shifts with the candidate, retain the first measurement and alternate already-warmed isolated revisions before attributing the shift to code. Logical workers on sibling hardware threads do not establish multicore scaling.

- Test stochastic policy identities across batch chunking and decoder instances. Replay of one batch cannot prove independence from transport order; batch-local indexes must not silently define the scientific randomization contract.
- For composed memory policies, test operand liveness as well as candidate equality: an upstream transformed prior or field must be consumed by the next policy, or the combination must be rejected.
