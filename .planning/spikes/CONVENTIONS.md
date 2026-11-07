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

## Tools and libraries

The project `.venv` supplies the pinned versions in `pyproject.toml`; no new dependency was installed for this spike.
