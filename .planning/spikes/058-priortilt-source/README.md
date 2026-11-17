---
spike: '058'
idea: priortilt-figure1
name: priortilt-source
type: standard
verdict: VALIDATED
related: ['057']
tags: [circuit, priortilt, figure1]
---

# Exact Fig1 artifacts and source contract

User-authorized scope: review project goals and reproduce Fig1 with canonical BP-family decoders, one CPU per point. Source and mathematical qualification precede production dispatch. Preserve prior evidence and phase gates.

## Research

Primary paper: https://arxiv.org/html/2611.13373v1
Author artifact repository: https://github.com/ionq-publications/PriorTiltDecoder

## Investigation Trail

Initial source review finds exact circuit artifacts, raw Fig1 measurements and optimized three-phase parameters available. Circuit memory is evaluated through detector/observable semantics rather than a CSS code-capacity substitute. PriorTilt is 60+3000x6 sweeps, RelayBP-1 is 80+300x60, and beam32_340iters is width32 with40 initial and10x30 continuation sweeps per path. The figure metric is (X-memory errors/shots + Z-memory errors/shots)/cycles.

## Results

Qualification findings are recorded below; no local LER reproduction claim yet.

## Verified source contract

The exact Fig. 1 corpus is 26 standard X/Z Stim memory circuits and 78 released per-basis result rows, combined into 39 source figure points. BB144 uses 12 cycles and p=.001/.002/.003/.004/.005; BB70 and GB102 use nine cycles and p=.0005/.0008/.001/.002. The BB144 noise is uniform circuit noise; the other panels use the released moving-qubit model without loss/leakage. The two XYZ files are outside scope. `source_contract.py` verifies each file SHA, detector/observable dimensions, one-to-one mechanisms, all source schedule/CSV identities and arithmetic, then reconstructs the figure from counts. No digitization or substitute noise model is needed.

The metric is `(errors_X/shots_X + errors_Z/shots_Z)/cycles`. It is not a pooled binomial rate and not automatic nonconvergence-as-failure. Source full-precision phase schedules supersede rounded paper table values. Beam's 340 sweeps are per path, with all discarded branches counted separately. Relay's 301 total legs mean 300 additional legs. Source artifacts and CC-BY-NC-SA license are kept separately from independently authored canonical policy code.

Both source Beam and Relay return the initial failed BP candidate if no later path converges. Their source-scoped canonical controllers implement this without editing the old CSS controlled-comparison controllers. The native detector-only merge shortcut causes no conflict on the target corpus: all 26 DEMs have zero duplicate detector supports. Their minimum check degrees16/28/39 remain above unary even after ten beam fixations.

Project fit: sparse transient priors are BP-internal policies, compatible with the existing binary min-sum engine. This user-requested circuit reproduction is an ad-hoc study and does not satisfy outstanding CSS/Pauli publication gates or change the roadmap sequence. Circuit exact/degenerate physical recovery is not observable from detector/observable samples; logical outcome and original detector validity are independently evaluated.

Evidence: [source manifest](../../../data/reproductions/priortilt-2611-13373/source.json), [machine source checks](../../../data/reproductions/priortilt-2611-13373/source-contract.json), [source counts](../../../data/reproductions/priortilt-2611-13373/source-figure1.csv), and [reconstructed figure](../../../data/reproductions/priortilt-2611-13373/source-figure1.png).

Verdict: VALIDATED for extraction and exact Fig. 1 artifact/configuration/metric identity. No local LER agreement claim follows from source extraction.
