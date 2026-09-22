# Walking Skeleton — Policy-Based BP Research Platform

**Phase:** 1  
**Generated:** 2026-09-21

## Capability Proven End-to-End

A researcher can run one source-linked CSS smoke fixture through strict preflight, pinned native BP, independent outcome evaluation, and a reloadable shot ledger. The fixture proves the architecture; Plan 09 adds the verified publication-code pilot.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Runtime | Python 3.12 `src/bp_registry` package | Inspectable scientific contracts and locally probed runtime. |
| Data layer | Versioned JSON records/manifests and append-only JSONL events | Human-inspectable source and shot history with explicit schema versions. |
| Native reference | Pinned `ldpc.BpDecoder` through `NativeBpReference` | Published binary BP implementation is an external reference; the canonical engine belongs to Phase 2. |
| Mathematical oracle | Project-owned GF(2) CSS validation and evaluator | Native convergence does not establish logical correctness. |
| Input identity | Raw and role/shape/order-sensitive semantic SHA-256 | Parameter labels alone cannot identify executable CSS matrices or logicals. |
| Authentication | None for the local research CLI | Phase 1 has no network user service or accounts. |
| Deployment target | Documented local Python command on the validated execution node | No hosted service or compute allocation was specified. |
| Directory layout | `src/bp_registry/`, `data/evidence/`, `data/artifacts/`, `data/manifests/`, `data/results/`, `tests/`, `docs/` | Keeps source evidence, immutable mathematical artifacts, execution, and checks distinct. |

## Stack Touched in Phase 1

- [ ] Project scaffold: `pyproject.toml`, collected pytest suite, observed environment pins.
- [ ] Entry point: `python -m bp_registry.cli` for validation, pilot, reconciliation, and inspection.
- [ ] Data read/write: source records and manifest read; begin/final JSONL and result JSON write.
- [ ] User interaction: local CLI command exposes source, artifact, shot, and result links.
- [ ] Local run: documented 32-shot selected CSS pilot after source/artifact verification.

## Later Slices

Phase 2 adds the project-owned canonical binary BP policy engine. Later phases add update, schedule, memory, intervention, selection, optional fallback, statistical, quaternary, and circuit capabilities in the ROADMAP order. Phase 1's pilot remains labelled `pilot_adaptation` and `not_assessed`.
