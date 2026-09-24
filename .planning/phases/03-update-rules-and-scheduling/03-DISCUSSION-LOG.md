# Phase 3: Update Rules and Scheduling - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-09-23
**Phase:** 03-Update Rules and Scheduling
**Areas discussed:** Update-rule parameters, Schedule order and stopping, Residual and cluster variants, Pilot comparisons

The user selected **all** four areas. Discussion used text questions, one decision at a time. The user approved writing the context after all four areas.

## Update-rule parameters

### How flexible should normalized min-sum's scaling factor and offset min-sum's offset be in Phase 3?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Fixed per run: explicit scalar parameters and source-linked presets. |  |
| 2 | Also vary by iteration: declared parameter sequences or formulas. |  |
| 3 | Also vary across the graph: check- or edge-specific parameters. | Yes |

**User's choice:** User: 'We may try decoder diversity so 3'. Support fixed, iteration-dependent, and check-/edge-specific parameters, recording resolved assignments.

### How should graph-specific parameters be supplied?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Explicit assignments and seeded generation. | Yes |
| 2 | Explicit assignments only. |  |
| 3 | Seeded generation only. |  |

**User's choice:** User selected 1: explicit assignments and seeded generation; parameter randomness remains separate from physical-error sampling.

### When should generated parameters refresh?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Fixed per decoder configuration across shots. |  |
| 2 | Fresh per shot/decoding attempt. |  |
| 3 | Configurable refresh: fixed, per attempt, or per iteration. | Yes |

**User's choice:** User selected 3: configurable refresh, supporting fixed per-configuration assignments, per-attempt draws, and per-iteration draws, with refresh rule and seed identity recorded.

### Should parameter exploration extend beyond published variants' stated ranges and assignment rules?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Allow explicitly labeled exploratory configurations. | Yes |
| 2 | Restrict to source-defined settings. |  |

**User's choice:** User selected 1: allow explicitly labeled exploratory configurations subject to mathematical and numerical validity checks; preserve source-defined presets separately.

### Continue with the next area or more on update-rule parameters?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Next area: schedule order and stopping. | Yes |
| 2 | More on update-rule parameters. |  |

**User's choice:** User selected 1: next area, schedule order and stopping.

## Schedule order and stopping

### Which serial update units should be available?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Check-node serial. |  |
| 2 | Check-node and variable-node serial. | Yes |
| 3 | Also individual-message serial. |  |

**User's choice:** User selected 2: check-node and variable-node serial as distinct schedules, each declaring fresh/stale message visibility.

### How should layered schedule membership be supplied?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Explicit partitions and automatic construction. | Yes |
| 2 | Explicit partitions only. |  |
| 3 | Source presets only. |  |

**User's choice:** User selected 1: explicit source/user partitions and deterministic graph-based automatic construction, with rules and resulting membership recorded and compatibility validated.

### When should randomized traversal order refresh?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Once per configuration across shots. |  |
| 2 | Once per attempt. |  |
| 3 | Configurable, including each sweep. | Yes |

**User's choice:** User selected 3: configurable refresh per configuration, per attempt, or per sweep. Traversal randomness is replayable and separate from parameter randomness and physical-error sampling.

### When should schedules check for convergence?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | After each complete sweep, with a declared residual boundary. |  |
| 2 | After each local update unit. | Yes |
| 3 | Configurable cadence. |  |

**User's choice:** User selected 2: after every completed local update unit, including each layer, serial node update, or residual-selected update; count every convergence check. Flooding retains its complete-sweep boundary. Hard work budgets are enforced independently of convergence-check cadence.

### Continue to residual and cluster variants or discuss scheduling further?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Next area: residual and cluster variants. | Yes |
| 2 | More on schedule order and stopping. |  |

**User's choice:** User selected 1: next area, residual and cluster variants.

## Residual and cluster variants

### Which source-selection approach should be used for residual and cluster-sequential scheduling?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Research and select a baseline for each. | Yes |
| 2 | Use sources the user will identify. |  |
| 3 | Implement multiple published variants for comparison. |  |

**User's choice:** User selected 1: research primary sources and select one well-specified source-linked baseline for each family, documenting selection rationale and unresolved details.

### How much experimental flexibility should accompany the residual baseline?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Baseline plus explicit exploratory variants. |  |
| 2 | Pinned baseline only. | Yes |

**User's choice:** User selected 2: pinned baseline only, exposing source-defined parameters without exploratory priority or selection rules in Phase 3. Residual evaluation and priority-maintenance work remain recorded.

### If the selected cluster source uses learned or optimized parameters, how should they be supported?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Load and regenerate them. |  |
| 2 | Load pinned artifacts only. | Yes |

**User's choice:** User selected 2: load pinned parameter artifacts only; defer reproducing any learning or optimization procedure. This applies conditionally to the selected source, not as an assumption that all cluster schedules use learning.

### How should pilot comparisons report schedule setup costs?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Separate setup and decoding costs. | Yes |
| 2 | Also show amortized costs for a declared number of shots. |  |

**User's choice:** User selected 1: report setup and decoding costs separately without assumed amortization. Unavailable costs of producing imported parameter artifacts remain explicitly unknown.

### Continue to pilot comparisons or discuss residual and cluster variants further?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Next area: pilot comparisons. | Yes |
| 2 | More on residual and cluster variants. |  |

**User's choice:** User selected 1: next area, pilot comparisons.

## Pilot comparisons

### How broadly should pilots exercise update-rule and schedule combinations?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Focused comparisons. | Yes |
| 2 | Every supported combination. |  |
| 3 | Source presets first. |  |

**User's choice:** User selected 1: focused comparisons, varying updates under flooding and schedules under sum-product before selected combinations and parameter-diversity examples. Use matched physical-error samples and explicitly reject undefined combinations; runs remain pilots.

### Which budget views should pilots provide?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Matched message-update caps. |  |
| 2 | Iteration-limited runs. |  |
| 3 | Both views. | Yes |

**User's choice:** User selected 3: both common check-to-variable message-update caps and schedule-qualified iteration limits. Report the full work vector and measured runtime, including residual, scheduling, and convergence-check overhead; no single counter is total cost.

### Which codes should pilots use beyond required small correctness fixtures?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Existing pinned BB-144 artifact. |  |
| 2 | BB-144 plus a verified HGP example. | Yes |

**User's choice:** User selected 2 and specified: "the family is HGP of 3,4 regular degree or PEG classical LDPC codes. BPGD paper has these"; user then added "also B1". Include existing pinned BB-144, the requested HGP family, and B1. Trace exact sources and pin code/logical artifacts before execution.

### How should pilot results be presented?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Tables and diagnostic plots. |  |
| 2 | Tables and machine-readable exports. |  |
| 3 | Tables, plots, and a runnable analysis notebook. | Yes |

**User's choice:** User selected 3: tables, diagnostic plots, and a runnable analysis notebook with outcome, iteration, work, runtime comparisons and selected convergence traces.

### Are any decisions still unclear?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Ready to write the Phase 3 context. | Yes |
| 2 | Explore more gray areas. |  |

**User's choice:** User selected 1: ready to write the Phase 3 context.

## Source follow-up

- User-referenced BPGD source checked: https://arxiv.org/html/2312.10950v2#S4.SS5. It reports B1 [[882,24,18<=d<=24]] and C2 HGP [[1922,50,16]]. The (3,4)-regular/PEG constituent construction was not established in this discussion and must be traced during research. C2 is a lead, not a confirmed match to that requested construction. Local code inventory still lists exact B1/C2 artifacts as unresolved.

## Agent's Discretion

- Research selects and justifies one residual baseline and one cluster-sequential baseline.
- Technical semantics, compatible artifacts, bounded pilot settings, and presentation details are resolved during research/planning within the recorded decisions.

## Deferred Ideas

- Decoder diversity motivates parameter flexibility now; ensemble execution remains in Phase 6.
- Reproduction of learning or optimization procedures for any imported source-defined cluster parameter artifacts is deferred; Phase 3 loads pinned artifacts only.
- Individual-message serial and exploratory residual selection rules were not selected for Phase 3.
- BPGD implementation and statistical campaigns retain their later roadmap placement.
