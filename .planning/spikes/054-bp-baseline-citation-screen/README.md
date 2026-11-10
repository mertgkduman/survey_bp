---
spike: '054'
idea: cited-bp-baselines
name: bp-baseline-citation-screen
type: standard
validates: Given candidate QLDPC decoding papers, when publication identities are resolved in one citation index, then a dated citation-prioritized shortlist can be inspected without adding duplicate editions.
verdict: PARTIAL
related: ['055']
tags: [literature, citations, bp, provenance]
---

# Spike 054: Citation screening for BP baseline papers

## What This Validates

A reproducible, dated citation screen supporting the user's request for the most cited QLDPC papers using min-sum or sum-product BP baselines. This is factual research rather than an application prototype. Its observable output is the ranked list and inspectable publication records, not a simulation or UI.

## Research

| Approach | Benefit | Limitation | Used |
|---|---|---|---|
| OpenAlex selected publication records | Machine-readable cited_by_count, stable work IDs and title/DOI metadata | Journal/preprint duplicates and imperfect metadata; counts are index-specific | Yes |
| Mixed publisher/Google Scholar/search snippets | Wider citation visibility | Different coverage, snapshot dates and edition merging make numeric ranks incomparable | No, not mixed into ranking |

Retrieved 10 November 2026 using title searches plus a 60-record descending-citation screen of titles containing quantum and abstracts mentioning belief propagation. Title searches also cover important works missed by that broad abstract query. The full query URLs and returned identities are in `search-screen.json`; selected raw publication metadata is in `citation-records.json`. These searches do not constitute an exhaustive systematic mapping study.

## How to Run

From the repository root:

```bash
.venv/bin/python .planning/spikes/055-bp-baseline-source-check/verify.py
```

Inspect `citation-records.json`, `search-screen.json`, and [the shortlist](../055-bp-baseline-source-check/PAPERS.md). Offline verification does not change the dated snapshot or query the network.

## Investigation Trail

1. Reused existing literature and kernel context for candidate discovery, while checking primary paper texts independently for this question.
2. Sampled OpenAlex rather than inferring prominence from familiar titles. One general search returned multiple editions of Poulin-Chung; switched to title screening and retained each work ID and edition caveat.
3. Added construction, survey-plus-method, trapping-set, Union-Find and hybrid candidates to avoid treating the existing registry as the complete literature.
4. Checked exact titles/authors/years. Panteleev-Kalachev is Quantum 5, 585 (2021), with a 2019 preprint. Rigby et al. is Phys. Rev. A 100, 012330 (2019). Kuo-Lai's 2020 journal article is distinct from its related scalar-message conference paper.
5. Observed a DOI formatting discrepancy for the OpenAlex Poulin-Chung record; kept its observed count but cross-checked paper identity against the primary text and correct publication metadata. No duplicate-edition counts were summed.
6. Distinguished Yao et al.'s counted ISIT 2024 record from the inspected longer arXiv v2. The numerical-baseline evidence is attributed to that full version.

## Results

**PARTIAL:** A dated ranking is available for the inspected candidate set; global top-N completeness and merged paper-level citation totals are not established. All reported counts use one selected OpenAlex record, avoiding incompatible databases or double-counting.

Seventeen papers are classified by Spike 055: twelve explicit standalone-BP comparisons, two foundational BP code benchmarks, two related hybrid papers, and one additional specialized min-sum hardware comparison. Related copies and unrelated quantum BP/QKD results in the broad screen are not automatically included.

No decoder, catalog, performance evidence, or publication gate changed. This screen does not authorize new HPC jobs or claim a completed literature mapping.
