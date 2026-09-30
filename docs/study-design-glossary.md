# Study-design glossary and work status

**Policy-Based BP Research Platform for QLDPC Decoding**

**Status date:** 30 September 2026

**Scope:** The planned first journal milestone covers CSS code-capacity, correlated quaternary code-capacity, and circuit-level decoding, in that order. This glossary describes the study design and the project's actual status on the date above. It is not a report of completed reproduction across those regimes. [Project scope](../.planning/PROJECT.md) · [Roadmap](../.planning/ROADMAP.md)

## How to read the colors

| Color and label | Meaning here | Claim boundary | Source |
| --- | --- | --- | --- |
| 🟩 **Executed** | Implemented, run, or independently checked at the scope stated in the entry. | A fixture or pilot is not automatically a paper reproduction or population estimate. | [State](../.planning/STATE.md) |
| 🟨 **On hold** | A specific study or source-dependent claim is cancelled, inconclusive, or waiting for a new qualification decision. | Retained partial evidence stays visible; it cannot silently become a completed denominator. | [Cancellation](../.planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md) |
| 🟦 **Future** | Planned, designed, or required, with no completed Phase 5-or-later implementation or qualifying study yet. | A plan describes intended work, not observed decoder behavior. | [Roadmap](../.planning/ROADMAP.md) |

The label applies to the **project treatment of a term**, not to whether the mathematical concept exists in the literature. An executed entry can have a narrow qualification: Phase 1's 32-shot native run is `pilot_adaptation` and `not_assessed`; Phase 4's completed mechanism gate does not establish a Relay circuit-curve reproduction. [Project](../.planning/PROJECT.md) · [Phase 4 verification](../.planning/phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md)

## Study sequence at a glance

| Workstream | Status | Design role and current boundary | Source |
| --- | --- | --- | --- |
| Phases 1–4: CSS foundation | 🟩 Executed | Initial literature map, native CSS baseline, canonical binary BP, update/schedule policies, memory policies, and Relay mechanisms have passed their phase gates. | [Roadmap](../.planning/ROADMAP.md) |
| Phase 5: guided interventions | 🟦 Future | Fourteen verified plans cover BPGD, impulse, freezing, syndrome/sign flips, restarting, and a bounded B1 mechanism pilot. No Phase 5 plan has executed. | [Phase 5 plans](../.planning/ROADMAP.md) |
| Cancelled Phase 4 comprehensive evaluation | 🟨 On hold | The oversized fresh evaluation and factorial were stopped. Their retained prefix is a receipt without a qualified comparison denominator; a later CSS campaign needs a new design. | [Cancellation](../.planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md) |
| Phases 6–9: CSS search, fallback, campaigns, comparison | 🟦 Future | Beam search, optional postprocessing, preregistered campaigns, and CSS reproduction/controlled comparisons remain staged work. | [Roadmap](../.planning/ROADMAP.md) |
| Phases 10–11: joint Pauli decoding | 🟦 Future | A compatible four-state kernel and matched correlated-versus-separate comparisons remain to be built and assessed. | [Roadmap](../.planning/ROADMAP.md) |
| Phases 12–13: circuit decoding | 🟦 Future | Detector/observable semantics, native/canonical circuit runs, and circuit-paper comparisons remain to be built and assessed. | [Roadmap](../.planning/ROADMAP.md) |
| Phase 14: completed map and manuscript | 🟦 Future | The full systematic map, supported-experiment release set, and three-regime journal evidence remain to be completed. | [Roadmap](../.planning/ROADMAP.md) |

## Research frame and comparison design

| Term | Status | Meaning in this study | Source |
| --- | --- | --- | --- |
| Systematic mapping protocol | 🟩 Executed | Versioned questions, search/screening, extraction, provenance, and an initial source-linked corpus. The completed map and publication cutoff are still future work. | [Requirements](../.planning/REQUIREMENTS.md) |
| Completed systematic map | 🟦 Future | The final selected corpus, flow/counts, extraction dictionary, limitations, and updated search through a declared cutoff. | [Phase 14](../.planning/ROADMAP.md) |
| Experiment registry | 🟩 Executed | A versioned manifest links a supported run to source identity, decoder settings, artifacts, samples, software, budgets, expected outputs, and discrepancies. The release-wide supported set is future work. | [Project](../.planning/PROJECT.md) |
| Canonical kernel family | 🟩 Executed | One inspectable binary CSS execution engine currently owns compatible BP policy behavior. A joint quaternary kernel and circuit integration require separate compatibility work. | [Architecture](../.planning/PROJECT.md) |
| Policy composition | 🟩 Executed | Explicit bindings for updates, schedule, memory, intervention, stopping, candidate selection, and postprocessing describe compatible decoder behavior. Some policy families remain future. | [Canonical engine](canonical-engine.md) |
| Source-faithful configuration | 🟦 Future | A paper-specific run must preserve its source-defined problem, algorithm, settings, implementation identity, and deviations before a reproduction claim. Source-qualified references already exist at narrower pilot scope. | [Project](../.planning/PROJECT.md) |
| Controlled comparison | 🟦 Future | A second analysis view holds samples, code, work limits, and evaluation rules common while varying declared decoder mechanisms. It answers a different question from paper-specific reproduction. | [Project](../.planning/PROJECT.md) |
| Matched physical samples | 🟩 Executed | Identified error draws can be reused across eligible arms so differences are attributable to policy choices. Existing pilots use this design; the Phase 5 B1 matched pilot is only planned. | [Phase 4 guide](phase4-memory-relay.md) |
| Preregistration and stopping rule | 🟦 Future | Freeze targets, tolerances, sample/work budgets, denominator rules, and stop criteria before publication campaigns; Phase 8 owns reusable campaign assessment. | [Roadmap](../.planning/ROADMAP.md) |

## Decoding problems and correctness

| Term | Status | Meaning in this study | Source |
| --- | --- | --- | --- |
| CSS code-capacity decoding | 🟩 Executed | Separate binary X/Z decoding on validated CSS check and logical matrices under identified data-error samples. Existing pilots are code-capacity adaptations. | [Project](../.planning/PROJECT.md) |
| Correlated quaternary decoding | 🟦 Future | Joint inference over I/X/Y/Z Pauli states with Y and X/Z correlations preserved in a mathematically compatible four-state kernel. | [Phase 10](../.planning/ROADMAP.md) |
| Circuit-level decoding | 🟦 Future | Decode noisy extraction circuits using detector and logical-observable semantics, not a relabeled CSS data-error model. | [Phase 12](../.planning/ROADMAP.md) |
| Check matrix and syndrome | 🟩 Executed | The binary parity-check matrix maps an error to observed parity violations; original syndromes are immutable inputs to outcome validation. | [CSS requirements](../.planning/REQUIREMENTS.md) |
| Ordered logical basis | 🟩 Executed | Logical operators and their pairing are part of a code artifact's identity, so a matrix with changed logical ordering is not treated as the same artifact. | [CSS requirements](../.planning/REQUIREMENTS.md) |
| Original problem | 🟩 Executed | The immutable observed decoding instance against which a selected recovery is judged, even if a policy solved a changed working instance. | [Canonical engine](canonical-engine.md) |
| Working problem and candidate lift | 🟦 Future | Phase 5 will transform priors, graph, or syndrome for an attempt and map a working-space candidate back to original coordinates with a checkable certificate. | [Phase 5 context](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-CONTEXT.md) |
| Exact recovery | 🟩 Executed | The selected recovery equals the sampled physical error; this is one independently evaluated outcome class. | [CSS requirements](../.planning/REQUIREMENTS.md) |
| Stabilizer-equivalent recovery | 🟩 Executed | A non-identical recovery can still have the same logical action as the sampled error; the evaluator distinguishes it from exact recovery. | [CSS requirements](../.planning/REQUIREMENTS.md) |
| Syndrome-valid logical failure | 🟩 Executed | A candidate matches the original syndrome but differs by a nontrivial logical operator; parity success alone does not imply decoding success. | [CSS requirements](../.planning/REQUIREMENTS.md) |
| Syndrome-invalid candidate | 🟩 Executed | A candidate fails the original parity check and cannot be promoted to success by convergence on a modified working syndrome. | [CSS requirements](../.planning/REQUIREMENTS.md) |

## BP policies and interventions

| Term | Status | Meaning in this study | Source |
| --- | --- | --- | --- |
| Message-update rule | 🟩 Executed | Sum-product, min-sum, normalized min-sum, and offset min-sum are explicit numerical policies with stated saturation, ties, and update semantics. | [Phase 3](../.planning/ROADMAP.md) |
| Schedule | 🟩 Executed | Flooding, layered, serial, residual, randomized, and source-defined cluster-sequential orders specify when fresh messages become visible and what work is counted. | [Phase 3](../.planning/ROADMAP.md) |
| Memory or damping policy | 🟩 Executed | Damping, mixing, momentum, iteration history, and disordered memory declare operands, order, lifetime, and reset behavior in the binary CSS engine. | [Phase 4 guide](phase4-memory-relay.md) |
| Relay-BP | 🟩 Executed | Source-linked multi-leg BP transfers a finite posterior-derived prior between legs and accounts for each leg and selection. Its completed Phase 4 gate is a mechanism result, not circuit-curve reproduction. | [Phase 4 verification](../.planning/phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md) |
| BPGD (guided decimation) | 🟦 Future | Planned source-qualified rounds select a reliable undecimated variable and change its prior while continuing BP. Zero/tie/final-round choices remain named interpretations. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Impulse decoding | 🟦 Future | Planned baseline-failure trigger launches bounded independent forced-bit attempts, records candidate origin/work, and selects after original-problem validation. Structural shortening is separately labeled adaptation. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Freezing | 🟦 Future | A bounded policy fixes eligible variables for a declared lifetime and records release or retry, rather than treating a temporary prior change as permanent truth. | [Phase 5 context](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-CONTEXT.md) |
| Syndrome flip | 🟦 Future | A source-linked attempt changes a working syndrome, carries a correction certificate, then checks the lifted result against the original observation. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Sign flip | 🟦 Future | A declared target, trigger, sign/magnitude convention, and state consequences distinguish a posterior perturbation from a changed channel prior or message. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Restarting | 🟦 Future | Explicit root/branch reset, preserved state, branch budget, and replay semantics. B1's exact distance is unknown, so its planned bounded restart is a mechanism adaptation. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Beam search and ensemble | 🟦 Future | Phase 6 will expose branch identity, masked BP, ranking/pruning, list selection, voting, and complete cost of accepted and discarded paths. | [Phase 6](../.planning/ROADMAP.md) |
| Optional OSD/LSD/SI/OTF | 🟦 Future | Phase 7 will attach source-qualified extra processing after declared BP nonconvergence while retaining a separately inspectable BP-only outcome. | [Phase 7](../.planning/ROADMAP.md) |

## Provenance, evidence, and study gates

| Term | Status | Meaning in this study | Source |
| --- | --- | --- | --- |
| Native reference | 🟩 Executed | A pinned author/library implementation can be run as an executable comparison with declared translation and unavailable internal counters. This status applies only to references actually pinned and run. | [Project](../.planning/PROJECT.md) |
| Unverified BPGD/impulse native identity | 🟨 On hold | Phase 5 research has not established an eligible exact author-code identity for these procedures; no unnamed package may be promoted to source-faithful reference. | [Phase 5 research](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-RESEARCH.md) |
| Experiment manifest | 🟩 Executed | A strict, versioned saved specification preflights decoder, code, sample, source, numerical, budget, and output identities before sampling. Phase 5 extends it only after execution. | [Registry requirements](../.planning/REQUIREMENTS.md) |
| Event ledger | 🟩 Executed | Per-shot and control-flow evidence records attempts, interventions, candidates, selection, termination, missingness, and typed work; optional detailed traces do not replace the ledger. | [Ledger requirements](../.planning/REQUIREMENTS.md) |
| Replay and independent verification | 🟩 Executed | A verifier reconstructs canonical terminal claims from persisted evidence while excluding nondeterministic timing from replay equality. New Phase 5 event semantics remain future. | [Canonical engine](canonical-engine.md) |
| Candidate lineage | 🟩 Executed | Stable IDs tie a selected original-space recovery to attempts, parents, and evidence without depending on append timing. | [Canonical engine](canonical-engine.md) |
| Pilot adaptation / `not_assessed` | 🟩 Executed | A runnable, source-linked mechanism pilot whose changed problem or settings are disclosed and whose outcomes carry no published-curve agreement verdict. | [Phase 1 pilot](phase1-pilot.md) |
| B1 Relay setting selection | 🟨 On hold | The completed Phase 4 calibration retained all terminal shots, but B1 had no eligible setting under its frozen work cap; no selected B1 Relay performance result follows. | [Phase 4 verification](../.planning/phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md) |
| Cancelled Phase 4 factorial and fresh evaluation | 🟨 On hold | The stopped comprehensive campaign retains partial receipts and explicit missingness. Later CSS assessment must be newly scoped rather than resumed or inferred from the prefix. | [Cancellation](../.planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md) |
| Phase 5 bounded B1 mechanism pilot | 🟦 Future | Plans use one common baseline plus six single-intervention arms on matched samples, with separate calibration, sealed caps, visible failed/denied attempts, and no decoder ranking. | [Phase 5 context](../.planning/phases/05-guided-and-perturbative-bp-interventions/05-CONTEXT.md) |
| Publication-curve reproduction | 🟦 Future | Statistical agreement with a paper's curve requires declared source settings, uncertainty, tolerance, denominator, and discrepancy assessment; bit-for-bit identity is not required. | [Project](../.planning/PROJECT.md) |
| Journal evidence package | 🟦 Future | The final manuscript and release must link the completed map, supported-paper manifests, open software, and qualified results from CSS, correlated quaternary, and circuit stages. | [Phase 14](../.planning/ROADMAP.md) |

## Outcome and resource vocabulary

| Term | Status | Meaning in this study | Source |
| --- | --- | --- | --- |
| Logical error rate (LER) | 🟩 Executed | A defined fraction of admitted shots with a logically wrong or unsuccessful selected recovery; interpretation depends on the stated denominator and problem regime. Existing bounded CSS pilot estimates are not paper-curve reproduction. | [Phase 4 guide](phase4-memory-relay.md) |
| Nonconvergence | 🟩 Executed | BP fails to meet its declared stop rule within a bounded attempt. It remains a visible terminal outcome and may later trigger an intervention or optional fallback. | [Canonical engine](canonical-engine.md) |
| Leaf work and total work | 🟩 Executed | Actual BP, branch/relay, candidate, and fallback work is recorded at unique leaf scopes and aggregated once; a denied operation cannot be counted as completed work. | [Ledger requirements](../.planning/REQUIREMENTS.md) |
| Runtime and resource context | 🟩 Executed | Iterations, wall time, CPU/resource observations, and native missingness retain units and scope; unlike work vectors, time is not a deterministic replay equality fact. | [Canonical engine](canonical-engine.md) |
| Inconclusive result | 🟩 Executed | A retained calculation that cannot meet its prespecified selection or statistical criterion under a cap; it is neither silently discarded nor reported as a pass. | [Phase 4 verification](../.planning/phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md) |
| Statistical campaign | 🟦 Future | Phase 8 will prespecify tolerances, sample budgets, stopping, shard verification, uncertainty, and acceptance before population-level or publication claims. | [Phase 8](../.planning/ROADMAP.md) |

## Rebuild and provenance

The Markdown is the editable source. Rebuild the color-coded PDF with `.venv/bin/python tools/build_study_design_glossary_pdf.py`; run the same command with `--check` to verify exact regenerated bytes. The PDF includes the status date, a text-plus-color key, and a digest of this Markdown source. Links above point to the repository's design and evidence records as of 30 September 2026. Later phase execution should update the glossary and regenerate its PDF together.
