# Spike Conventions

Patterns established by this presentation reproduction session.

## Stack

Use the project's Python, NumPy, SciPy, Numba, and Matplotlib environment for decoder feasibility and plots.

## Structure

Keep presentation source values, decoder policy files, local measurements, and plots together under the user-requested `from_dr_pfister_presentetations/` folder. Store GSD investigation trails under `.planning/spikes/`.

## Patterns

- Label every number as reported source data or local measured data.
- Use deterministic paired error streams, per-shot JSONL ledgers, seed and denominator fields, and ledger hashes.
- Verify CSS code parameters and stabilizer/logical outcome semantics before interpreting decoder rates.
- Mark unspecified source numerical choices as assumptions; never call an adaptation a source-faithful reproduction.

## Tools and libraries

The project `.venv` supplies the pinned versions in `pyproject.toml`; no new dependency was installed for this spike.
