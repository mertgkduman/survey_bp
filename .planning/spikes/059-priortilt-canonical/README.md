---
spike: '059'
idea: priortilt-figure1
name: priortilt-canonical
type: standard
verdict: VALIDATED
related: ['057']
tags: [circuit, priortilt, figure1]
---

# Canonical PriorTilt policy semantics

User-authorized scope: review project goals and reproduce Fig1 with canonical BP-family decoders, one CPU per point. Source and mathematical qualification precede production dispatch. Preserve prior evidence and phase gates.

## Research

Primary paper: https://arxiv.org/html/2611.13373v1
Author artifact repository: https://github.com/ionq-publications/PriorTiltDecoder

## Investigation Trail

Initial source review finds exact circuit artifacts, raw Fig1 measurements and optimized three-phase parameters available. Circuit memory is evaluated through detector/observable semantics rather than a CSS code-capacity substitute. PriorTilt is 60+3000x6 sweeps, RelayBP-1 is 80+300x60, and beam32_340iters is width32 with40 initial and10x30 continuation sweeps per path. The figure metric is (X-memory errors/shots + Z-memory errors/shots)/cycles.

## Results

Qualification findings are recorded below; no local LER reproduction claim yet.

## Qualified implementation

`canonical/prior_tilt.py` adds the Eq.3–7 policy controller over the existing canonical min-sum sweep; no existing kernel file changes. Statistics cover the final six initial sweeps and each subsequent six-sweep round, including posterior and outgoing V2C extrema. Offsets replace the previous offset against the immutable original prior, stay fixed within a round, and never reset message state. Full-precision source schedules use strict round boundaries and per-node/per-round indexed randomness, stable across batching and decoder instances. Work includes every sweep/edge and typed random-draw/biased-node operands, plus offset/gamma lineage hashes.

`circuit/paper_decoders.py` implements the source-specific Beam/Relay control semantics using that same sweep. Independent Python conditioned-subproblem/frontier and memory oracles check fixed-variable syndrome adjustment, inherited messages, posterior memory, pruning/ties, initial-failure fallback and all-path directed updates. Native reference comparisons use pinned F64 author binaries, independently built in isolated `/tmp` directories. Reference binaries are never used by the campaign.

The initial strict terminal-state comparison failed and is preserved in `native-initial-probe.json`; it must not be presented as a numerical-identity pass. The isolated ordinary-BP probe with exactly aligned priors shows maximum absolute belief differences of 0 at one sweep, 5.26e-13 by six, 1.17e-11 by12 and 5.39e-7 by36. PriorTilt's perturbed probe reaches 1.94e-4. Canonical total-minus-excluded-message arithmetic versus author prefix/suffix arithmetic explains a numerical boundary already present before offsets. We retain the canonical order instead of introducing another BP kernel. All144 ordinary-only probe candidates/stopping decisions match; all72 PriorTilt candidates/stopping/eligible counts match. All72 baseline cases match candidate/convergence; Relay additionally matches all-path sweeps, chosen posterior and explicit same gamma fields. Native Beam lacks an equivalent all-path work counter; independent oracles provide that check. Distribution-preserving policy RNG differs from native RNG.

Final full-budget qualification samples all26 circuits ×three methods ×eight shots=624 events on separate seeds. Original-DEM detector/observable equations and each path's budget/work are checked independently. These shots are qualification-only, never production measurements or source LER claims. See `qualification.json` and its hash-bound compressed event ledger in the study directory.

Verdict: VALIDATED for the independent mathematical policy, source-scoped controller semantics and declared canonical adaptation. Bitwise native terminal-state equality and statistical Fig.1 reproduction are outside this verdict.
