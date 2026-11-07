---
spike: 010
idea: canonical-kernel-audit
name: policy-extensibility
type: standard
validates: "Given supported policy compositions, when exercised, then order, state isolation, and compatibility are explicit"
verdict: PARTIAL
related: [008-mathematical-correctness, 009-open-source-cross-check, 011-execution-consistency]
tags: [policies, architecture, composition]
---

# Spike 010: Policy extensibility

## What This Validates

Whether policies compose without silently losing an admitted operation, and whether the implementation has sufficient extension boundaries for the requested BP families.

## Research

The project contracts are the authority for policy ownership. For an external architectural comparison, [NVIDIA Sionna's versioned BP decoder API](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) separates node update functions, schedules, V2C/C2V callbacks, clipping, and state return. This is an interface comparison only; no Sionna decoder was installed or executed.

| Approach | Strength | Limitation | Chosen use |
|---|---|---|---|
| Existing per-policy tests | Broad lifecycle and mechanism coverage | Can miss interactions with changed numerical defaults | Run 238 existing tests |
| Identity and sensitivity probes | Detect silent composition changes | Do not prove arbitrary combinations | New 12 grouped probes |
| Source call-path review | Exposes duplicated recurrence ownership | Must support defects with execution | Locate failed metamorphic paths |

## How to Run

```sh
OMP_NUM_THREADS=1 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/010-policy-extensibility/probe.py
```

The regression file list is preserved in `regression.xml` and summarized below. Run pytest against the listed contract/memory/relay/schedule/intervention/candidate-selection files plus quaternary BPGD, MBP4, schedules, and public-execution tests; use the recorded XML test paths to reconstruct the exact selection.

## What to Expect

New probes: 12 grouped checks, 9 pass, 3 findings. Existing regression selection: **238 passed in 17.13 s**. Passing regressions do not override the newly demonstrated composition failures.

## Observability

`results.json` records numerical deltas, admission equations, environment/source hashes, and counterexamples. `regression.xml` and `regression.log` retain every existing test identity and outcome.

## Investigation Trail

1. Used an identity C2V normalization (divide by 1) as a metamorphic test. Frozen BP4 v1 preserves all buffers. BP4 v2 preserves first-sweep C2V and beliefs but changes V2C: `QbpFloodingSchedule._transformed_sweep` does not apply `profile.v2c_damping`, while `QbpSession.sweep` does. Subsequent sweeps can therefore diverge merely by adding an identity transform.
2. Compared serial BP4 with damping 0 and 0.6. Its V2C outputs are identical: the serial implementation also omits damping. The resolver nevertheless declares the v2 damping equation for these admitted compositions. This is a concrete execution/evidence defect, not merely an unsupported feature.
3. Verified normalization/offset order is observable: on -3, normalization by 2 then offset .75 yields -.75; reverse order yields -1.125. Order must remain part of evidence.
4. Verified independent session state, unchanged original checks, foreign memory-commit rejection, and rejection of binary schedule/transform names and undefined adaptive MBP4 in the quaternary resolver.
5. Direct `BinarySpaKernel(update_rule=MinSumUpdate())` accepts a v1 min-sum primitive with the default SPA-v2 numerical profile. The check rule clips at 25 while surrounding v2 state is unclipped and damped. This may be an explicitly intended adaptation, but the low-level constructor does not require that identity or reject the ambiguity. The public closed registry is a separate boundary.
6. Ran 238 existing tests covering contracts, memory compositions and local memory, relay and native translation, flooding/local/residual/cluster schedules, perturbative interventions, candidate/list selection, Q-BPGD, MBP4, and quaternary public execution. All pass.

## Capability Matrix

| Mechanism | Existing implementation | Qualification boundary |
|---|---|---|
| Binary SPA/MS/NMS/OMS | Check-update protocol, indexed parameter assignments | Low-level numerical-profile/update compatibility needs enforcement |
| Flooding/layered/check-serial/variable-serial | Separate explicit freshness and commit semantics | Do not treat equal sweep counts as equal work |
| Residual/randomized/cluster schedules | Dedicated schedule modules and tests | Memory registry intentionally excludes residual/cluster combinations |
| Damping/affine memory/PDBP/PD-prime/momentum | Typed proposals, owned histories and declared boundaries | Broad binary support; v2 quaternary damping omitted by two schedule paths |
| Decimation/freezing/perturbation | Binary intervention controllers and Q-BPGD | Source-specific restart versus continued-message semantics remain distinct |
| Relay/branch/beam/list selection | Engine lifecycle and independent candidate evaluation | Full engine/public evidence must be checked separately from fast kernels |
| Quaternary normalization/offset and fixed-alpha MBP4 | Dedicated transforms and MBP4 recurrence | Not arbitrary binary ports; adaptive MBP4 remains rejected |
| Low-precision/resolution policies | Compiled flooding policy route | Float64 intermediates with boundary quantization; not native low-precision execution |

## Results

**PARTIAL.** The policy architecture is substantial and covers the requested categories, but it is not ready to freeze as universally composable. Identity-transform invariance and declared damping sensitivity fail in actual admitted v2 paths.

Stabilization should centralize the ordered update stages shared by plain/transformed/serial paths, with explicit operands and freshness rather than one generic callback that can mutate everything. Add admission constraints per kernel/profile/schedule, and require each implementation backend to pass the same semantic fixtures. Keep source-specific algorithm names and adapted compositions distinct. New policies should supply equations, owned state, read/write operands, commit boundary, reset/clone behavior, and work charges without duplicating the entire BP sweep.
