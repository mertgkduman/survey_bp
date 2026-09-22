# Phase 1: Evidence Registry and Native CSS Baseline - Pattern Map

**Mapped:** 2026-09-21  
**Files analyzed:** 19 proposed new/modified files  
**Analogs found:** 0 / 19

## Scope Basis

Phase 1 is a greenfield implementation. `01-CONTEXT.md` explicitly says no project implementation exists, and the tracked repository contains planning and research documents only. Consequently, no implementation analog or code excerpt is available to copy. The paths below are the proposed `src/`, `data/`, and `tests/` layout from `01-RESEARCH.md`; the planner may consolidate or rename them while retaining the listed responsibility boundaries.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `pyproject.toml` | config | transform | — | none |
| `src/bp_registry/__init__.py` | config | transform | — | none |
| `src/bp_registry/evidence.py` | model | CRUD | — | none |
| `src/bp_registry/manifests.py` | model | file-I/O | — | none |
| `src/bp_registry/css.py` | model | transform | — | none |
| `src/bp_registry/artifacts.py` | service | file-I/O | — | none |
| `src/bp_registry/sampling.py` | service | transform | — | none |
| `src/bp_registry/reference.py` | service | request-response | — | none |
| `src/bp_registry/evaluator.py` | service | transform | — | none |
| `src/bp_registry/ledger.py` | service | event-driven | — | none |
| `src/bp_registry/runner.py` | controller | event-driven | — | none |
| `src/bp_registry/cli.py` | controller | request-response | — | none |
| `data/evidence/protocol.json` | config | CRUD | — | none |
| `data/evidence/seed-records.json` | model | CRUD | — | none |
| `data/artifacts/` (frozen CSS matrices/logicals and metadata) | model | file-I/O | — | none |
| `data/manifests/gross-bb144-pilot.json` | config | file-I/O | — | none |
| `tests/test_evidence.py` | test | CRUD | — | none |
| `tests/test_manifest.py`, `tests/test_reference_smoke.py` | test | request-response | — | none |
| `tests/test_css_small.py`, `tests/test_sampling.py`, `tests/test_ledger.py` | test | transform/event-driven | — | none |

## Pattern Assignments

### `pyproject.toml` and `src/bp_registry/__init__.py` (config, transform)

**Analog:** none.

Create the initial Python package and pytest configuration during Wave 0. The research specifies Python 3.12.2 and records locally probed NumPy, SciPy, `ldpc`, and pytest versions; package pins must record the environment actually tested. `pydantic` and `bposd` are proposed installs and require the research-mandated human legitimacy checkpoint before installation.

### `src/bp_registry/evidence.py`, `data/evidence/protocol.json`, and `data/evidence/seed-records.json` (model/config, CRUD)

**Analog:** none.

Build strict, versioned records for works, revisions, search events, screening/adjudication history, source claims, experiment/curve extraction, ambiguity, and evidence state. Preserve raw search-hit IDs alongside normalized work IDs. Seed BPGD and impulse records must fully extract CSS code-capacity material while recording quaternary and circuit material as identified but deferred.

### `src/bp_registry/manifests.py` and `data/manifests/gross-bb144-pilot.json` (model/config, file-I/O)

**Analog:** none.

Use a strict versioned manifest that includes paper/revision/figure anchors, ordered code and logical hashes, decoder parameters, noise/rates, seed derivation, budget/stopping, versions, expected-output/tolerance status, discrepancies, and `pilot_adaptation` lineage. Validation must reject unknown fields, malformed or out-of-range values, mutable or missing inputs, and hash failures before a decoder is called. A pilot that has no curve criterion must persist `expected_output_status=not_assessed` and its reason.

### `src/bp_registry/css.py` and `src/bp_registry/artifacts.py` (model/service, transform/file-I/O)

**Analog:** none.

Separate CSS algebra from artifact loading. The algebra module owns GF(2) rank, check commutation, ordered paired-logical validation, row-space membership, and canonical semantic byte serialization. The resolver loads only content-addressed artifacts below the approved artifact root, verifies raw and semantic SHA-256 identities, prevents path escape, and refuses unverified source identity. Do not use real-valued matrix rank.

### `src/bp_registry/sampling.py` and `src/bp_registry/evaluator.py` (service, transform)

**Analog:** none.

The sampler derives each physical-error seed from manifest identity plus stable shot ID and creates identified X-only bit-flip samples with separately named X/Z check observations. The evaluator, rather than the native adapter, receives hidden truth and classifies candidates as `invalid_syndrome`, `exact`, `stabilizer_equivalent`, or `logical_failure` against the immutable original problem. It must test both GF(2) row-space membership and paired logical action on small fixtures.

### `src/bp_registry/reference.py` (service, request-response)

**Analog:** none in the repository; implementation guidance comes from `01-RESEARCH.md` lines 205-220.

Wrap the pinned native `ldpc.BpDecoder` only. Configure explicit error rate, maximum iterations, product-sum method, parallel schedule, syndrome input, and one OpenMP thread; return candidate, `converge`, and `iter`. Record unavailable native counters as null with an `unavailable_reason`. The adapter receives only checks, syndrome, prior, and decoder-local randomness; it never receives sampled truth and provides no OSD fallback in this pilot.

### `src/bp_registry/ledger.py` and `src/bp_registry/runner.py` (service/controller, event-driven)

**Analog:** none.

Use typed versioned JSONL with idempotent `run_id`/`shot_id`. The runner writes a begin event before sampling, invokes artifact preflight, sampling, native reference execution, and independent evaluation, then writes one terminal record. Reconciliation turns an unmatched begin into an `interrupted` terminal record after catchable interruption or restart. Keep convergence, selection, termination, outcome, and post-selection distinct; never infer unavailable native internals or treat a SIGKILL as observed decoder termination.

### `src/bp_registry/cli.py` (controller, request-response)

**Analog:** none.

Expose bounded local commands for protocol/registry validation, manifest preflight, pilot execution, and ledger reconciliation. CLI inputs must remain within the approved artifact root and bounded matrix/shot budgets before file loading, supporting the local research threat model.

### Test files (test; CRUD, request-response, transform, and event-driven)

**Analog:** none.

Follow the validation contract in `01-VALIDATION.md`: evidence history reload and ambiguity tests; strict preflight rejection before decoder invocation; a tiny native syndrome smoke test; GF(2), order-sensitive hash, sampling, and four-outcome fixtures; and begin/terminal ledger reconciliation for success, nonconvergence, exception, and interruption. The quick suite is `python -m pytest -q tests/test_css_small.py tests/test_manifest.py tests/test_reference_smoke.py` after Wave 0; the full suite is `python -m pytest -q`.

## Shared Patterns

### Provenance and evidence status

**Source:** tracked [`01-CONTEXT.md`](01-CONTEXT.md) and [`01-RESEARCH.md`](01-RESEARCH.md), not implementation code.

Apply to registry, manifest, runner, ledger, and presentation records. Source-linked claims, unresolved identities, interpretation decisions, and source-faithful versus pilot-adaptation status must remain explicit. Execution promotes a run to `reference_executable` only; it does not establish `canonical_implemented` or `statistically_assessed`.

### Immutable-problem boundary

**Source:** tracked [`01-RESEARCH.md`](01-RESEARCH.md), Architectural Responsibility Map and Architecture Patterns, not implementation code.

Apply to sampler, reference adapter, evaluator, runner, and tests. Keep full error truth in runner/evaluator; pass only the syndrome and validated decoder inputs to the native adapter; independently score the returned candidate against original checks and logicals.

### Strict preflight and artifact integrity

**Source:** tracked [`01-RESEARCH.md`](01-RESEARCH.md), Artifact resolver and Artifact bytes and identity sections, not implementation code.

Apply to manifest, resolver, runner, and CLI. Validate schema and cross-field constraints before execution, resolve only approved-root immutable artifacts, preserve ordered matrix/logical bytes, and verify raw plus semantic SHA-256 hashes before sampling.

### Event-complete persistence

**Source:** tracked [`01-RESEARCH.md`](01-RESEARCH.md), Ledger and evidence transitions section, not implementation code.

Apply to runner and ledger. Each begun shot has exactly one reconcilable terminal status; retain failures, nonconvergence, exceptions, and interruptions for denominator audits.

## No Analog Found

All Phase 1 implementation files have no close code analog because the codebase is intentionally greenfield. The planner should use the source-linked contracts in `01-RESEARCH.md`, the required verification cases in `01-VALIDATION.md`, and the requirements MAP-01–03, REG-01–04, CSS-01–04, and LED-01 rather than copy implementation excerpts.

## Metadata

**Analog search scope:** tracked repository files outside `.git`; searched planning, research, phase, source, test, and configuration paths.  
**Files scanned:** 19 tracked project/planning files; 0 implementation source files and 0 test files existed.  
**Pattern extraction date:** 2026-09-21.  
**Tracked-source gate:** No analog paths emitted. All documentary sources named above are tracked (`git ls-files` verified).
