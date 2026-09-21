<!-- GSD:project-start source:PROJECT.md -->

## Project

**Policy-Based BP Research Platform for QLDPC Decoding**

An open, accessible, and interpretable research platform for BP-family quantum low-density parity-check (QLDPC) decoders, paired with a systematic mapping study of the literature and an executable registry of published experiments. Within each mathematically compatible BP kernel family, one canonical execution engine expresses decoder behavior through explicitly defined modular policies rather than merely wrapping unrelated implementations behind a shared API. The platform, literature study, and experiments will support a journal paper covering CSS code-capacity decoding, correlated quaternary code-capacity decoding, and circuit-level decoding, developed in that order.

**Core Value:** Make BP decoder differences explicit, reproducible, and fairly comparable by expressing compatible algorithms as policy compositions in a canonical execution engine and linking their measured behavior to published evidence.

### Constraints

- **Architecture**: One canonical execution engine per mathematically compatible kernel family — scientific interpretability and fair comparison require more than adapter-level integration.
- **Priority**: BP-internal policies and named BP modifications before optional OSD/LSD-style postprocessing — this is the user's principal research focus.
- **Sequence**: CSS code-capacity before correlated quaternary code-capacity before circuit-level decoding — complexity must be introduced in stages without shrinking the publication scope.
- **Reproduction**: Statistical agreement with published curves is sufficient — bit-for-bit identity is not required, but discrepancies must be documented.
- **Provenance**: Every simulation must emit an event ledger, and every supported paper must have a reproduction manifest — evidence must remain traceable through analysis and publication.
- **Comparison**: Preserve both paper-specific and controlled configurations — reproduction and fair cross-decoder comparison answer distinct research questions.
- **Accessibility**: Deliver open software and detailed documentation — exact license, packaging, interface, implementation languages, and backend choices remain undecided.
- **Resources**: The current workspace is on an HPC filesystem — concrete compute allocations, runtime budgets, and scheduling requirements have not yet been specified.
- **Publication**: The journal paper includes all three decoding regimes — target journal, submission date, and manuscript format remain undecided.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

The stack is a research recommendation, not an installed environment or dependency lock. See `.planning/research/STACK.md` and its reconciled findings in `.planning/research/SUMMARY.md`.

- Start with inspectable Python kernels and NumPy/SciPy; validate Python/library versions and HPC compatibility before pinning.
- Keep native decoder dependencies and environments separate from canonical policy execution.
- Use versioned machine-readable manifests and typed shot/event ledgers; select concrete schema and storage dependencies during implementation.
- Add Stim/Sinter integration at the circuit stage with explicit detector/observable semantics.
- Consider compiled kernels only after profiling, while preserving the canonical behavioral contract and evidence.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Read `.planning/STATE.md`, `.planning/PROJECT.md`, and the current phase before work. Implementation conventions will be established during Phase 1.

- Cite primary sources for mathematical algorithms; record interpretive decisions and unresolved source details.
- Statistical curve reproduction does not replace independent algebraic and policy-semantics checks.
- Prespecify tolerances, budgets, stopping and denominator rules before publication campaigns; retain failed/inconclusive evidence.
- Preserve the approved autonomous mode, fine phases, parallel independent work, and saved Codex role model/effort settings in `.planning/config.json`.
- All three decoding regimes remain in the first journal milestone. BP modifications precede substantial optional fallback implementation.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

This is a new project; no implementation exists yet. The proposed architecture is in `.planning/research/ARCHITECTURE.md`, with staged delivery in `.planning/ROADMAP.md`.

- Own one canonical execution engine per compatible mathematical BP family; native decoder adapters are executable references.
- Keep original problems immutable. Decoder policies cannot inspect hidden simulation truth; independent evaluators judge original-problem outputs.
- Record policy equations/order, compatibility, numerical conventions, scoped stopping, candidate lineage, and all branch/relay/fallback work.
- Keep CSS/Pauli recovery semantics separate from circuit detector and logical-observable semantics; mark undefined metrics not applicable.
- Require manifests and per-shot/control-flow provenance. Detailed per-edge traces are optional; missing native instrumentation is explicit.
- Distinguish source-faithful reproduction, canonical adaptation, controlled comparisons, and mapped-only literature evidence.

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `$gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `$gsd-debug` for investigation and bug fixing
- `$gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `$gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
