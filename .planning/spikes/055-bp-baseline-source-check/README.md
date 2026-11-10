---
spike: '055'
idea: cited-bp-baselines
name: bp-baseline-source-check
type: standard
validates: Given citation-prioritized candidates, when primary methods and numerical comparisons are inspected, then standalone BP baselines can be distinguished from code benchmarks and hybrid decoders.
verdict: VALIDATED
related: ['054']
tags: [literature, bp, min-sum, sum-product, baseline]
---

# Spike 055: Verify BP baseline evidence in primary papers

## What This Validates

The user requested papers, accepting either min-sum or sum-product BP. The factual output is [PAPERS.md](PAPERS.md), with an inspectable [JSON](papers.json) / [CSV](papers.csv) record for each inclusion, its primary source, evidence location, update family, citation provenance and edition caveats.

## Research

Citation prominence alone cannot show that a paper actually reports a standalone BP comparison. Primary methods, equations, simulation sections and figure captions are checked separately. A paper is included in the twelve-paper core only when ordinary BP or a declared BP-family baseline is explicitly evaluated. Code-construction benchmarks and BP+OSD/BP+SSF hybrid experiments remain separate categories.

The standard Python verifier checks artifact consistency. No decoding experiment, application UI, or implementation probe is needed to answer this literature question. Primary arXiv HTML, publisher pages and the Babar et al. full primary PDF were inspected. Pypdf was installed into an isolated `/tmp` tools directory to inspect that large PDF after the web reader could not retrieve it; this added no repository or project-environment dependency. No copyrighted paper copies are committed.

## How to Run

```bash
.venv/bin/python .planning/spikes/055-bp-baseline-source-check/verify.py
```

Read [PAPERS.md](PAPERS.md) for the human-facing list. Follow each primary source and evidence locator to inspect the actual comparison. Citation counts are the 10 November 2026 snapshot from Spike 054, not Google Scholar totals.

## Investigation Trail

1. Verified Panteleev-Kalachev Fig. 1 as BP versus BP-OSD-0 and located the normalized min-sum/layered simulation settings. This is not a generic unspecified SPA result.
2. Verified Roffe et al. Fig. 3 as standalone BP versus BP+OSD-CS; Appendix C defines variable-scaled min-sum.
3. Verified probability/log-domain sum-product baselines in Poulin-Chung, Liu-Poulin, Wang et al., Kuo-Lai and Rigby et al. The update names alone do not prescribe all numerical or stopping conventions.
4. Confirmed Babar et al. is not only a survey: Sec. VII A and Fig. 16 (PDF page 21) compare binary and standard non-binary BP with modified decoding on an 800-qubit bicycle code.
5. Added Raveendran-Vasic Fig. 10's flooding-versus-layered min-sum comparison. Added Delfosse et al. Fig. 4's Union-Find versus BP comparison; the log-domain tanh/atanh appendix identifies a sum-product-type implementation. Its exact conventions still require a separate reproduction review.
6. Confirmed Yao et al.'s binary BP baselines use sum-product and its full version reports ordinary Q-BP versus Q-BPGD. Imported BP-OSD/BP-SI comparison points are not mislabeled as its ordinary BP runs.
7. Classified MacKay et al. and Hagiwara-Imai as foundational code benchmarks using ordinary SPA, rather than new-decoder-versus-BP comparisons.
8. Kept Bravyi et al.'s highly cited BP-OSD circuit-memory paper separate. Grospellier et al. use sum-product BP within BP+SSF and principally benchmark SSF; use of the BP component alone does not certify a reported standalone BP curve.
9. Checked the ranked JSON/CSV, source locations, unique identities, citations and category membership using the offline verifier. Source interpretation was checked by reading primary papers; the verifier alone does not establish those semantic claims.

## Results

**VALIDATED for the bounded shortlist:** twelve explicitly documented standalone-BP comparisons, plus clearly labeled contextual papers. The result is suitable for choosing papers to extract into reproduction manifests, not a guarantee that every source supplies all settings or artifacts needed for reproduction.

Top core citation records in this snapshot are Panteleev-Kalachev (337), Roffe et al. (289), Poulin-Chung (165), Babar et al. (117), and Liu-Poulin (110). The more highly cited Bravyi et al. hybrid record (711) and foundational MacKay et al. code benchmark (403) remain visible in separate sections. This prevents citation rank from silently changing the meaning of baseline.

No measured results, backend implementation, public interface, model configuration or scientific phase status changed. No simulation or experiment request was submitted.
