# Literature BP policy registry

This directory collects source-grounded descriptions of BP-family decoders before their reproduction campaigns. Create one folder per **paper revision**, named `<first-author>-<year>-<short-title>`. Start from [`_paper-template/`](./_paper-template/), then add one TOML file directly in the paper folder for each requested decoder variant. A variant in a paper is a source identity; it is not automatically an executable policy composition.

## Each paper folder

- `<variant>.toml`: a **runnable** declarative decoder file using the installed `bp-registry` policy schema. Put it directly in the paper folder once its policy kinds and compatibility have passed preflight and focused equation/transition checks.
- `<variant>.spec.toml`: a **non-runnable source specification**, also directly in the paper folder, when its proposed policy composition has not yet passed executable-registry qualification. Record known equations, ordering, parameters, and explicit blockers. This file is research evidence and is not an input to `bp-registry` until it is validated and converted to a runnable file.
- `paper_reproduction/`: the citation, exact revision and primary-source links, author-code revision, equation/algorithm anchors, decoder status and unresolved details, plus code, circuit, noise, and reported-result identities. Keep source-specific settings and adaptation decisions here so the decoder TOML can be reused in other study settings.

The first CSS gate has three papers: [Yao BPGD](./yao-2024-guided-decimation/paper_reproduction/PAPER.md), [Bhatnagar impulse](./bhatnagar-2026-impulse-decoding/paper_reproduction/PAPER.md), and [Rabeti–Mahdavifar MBBP-LD](./rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/PAPER.md). Their 14 `.spec.toml` source records remain non-runnable. Qualified canonical adaptations are separate paper-root `.toml` files. The common parser keeps equations, references, and explanations as provenance while compiling only registered policy controls. A runnable adaptation is still `not_assessed` against the published curve.

```text
literature_policies/<paper-id>/
  <decoder-a>.toml
  <decoder-b>.spec.toml
  paper_reproduction/
    PAPER.md
```

Keep one source-specific variant per file when parameters or procedure differ materially. A controlled adaptation gets its own clearly named file and source-status entry in `paper_reproduction/PAPER.md`. Do not silently fill missing parameters or equate a CSS adaptation with a circuit-paper reproduction.

## Status path

1. **Mapped only:** the paper and variant are indexed; source details and missing facts are explicit.
2. **Specified:** equations, update order, state lifetime, stopping, selection, and parameter meaning have independent source anchors.
3. **Implemented:** a compatible kernel and registered policies exist; the TOML file passes manifest preflight and focused mathematical checks.
4. **Evaluated:** a study manifest pins code/circuit, noise, seeds, budgets, expected outputs, tolerances, and denominator rules; results have a verified ledger.
5. **Reproduced or discrepant:** the prespecified statistical comparison with the paper is assessed. A runnable file alone never establishes reproduction.

The public `bp-registry` command runs registered canonical CSS compositions, ordered memory/Relay, qualified Phase 5 guided-decimation and impulse interventions, the Phase 6 MBBP-LD ensemble, and the special BB72 BeamSearch/RelayBP campaign. Coordinate-majority voting has a tested kernel primitive but is rejected by the public MBBP manifest until its execution and replay contract is implemented. Arbitrary new policy equations, correlated quaternary inference, and circuit decoding require their later phases. See the [researcher command guide](../docs/researcher-study-command.md).

We will collect source statements about codes, circuits, noise, and published curves **while extracting each policy** because those details can determine the algorithm's meaning. The immutable artifacts and reproduction manifests can follow as their roadmap phases mature: CSS reproduction (Phase 9), quaternary execution/reproduction (Phases 10–11), and circuit execution/reproduction (Phases 12–13). The mapping study continues through Phase 14.
