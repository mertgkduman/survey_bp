# Literature BP policy registry

This directory collects source-grounded descriptions of BP-family decoders before their reproduction campaigns. Create one folder per **paper revision**, named `<first-author>-<year>-<short-title>`. Start from [`_paper-template/`](./_paper-template/), then add one TOML file directly in the paper folder for each requested decoder variant. A variant in a paper is a source identity; it is not automatically an executable policy composition.

## Each paper folder

- `<variant>.toml`: a **runnable** declarative decoder file using the installed `bp-registry` policy schema. Put it directly in the paper folder once its policy kinds and compatibility have passed preflight and focused equation/transition checks.
- `<variant>.spec.toml`: a **non-runnable source specification**, also directly in the paper folder, when its proposed policy composition has not yet passed executable-registry qualification. Record known equations, ordering, parameters, and explicit blockers. This file is research evidence and is not an input to `bp-registry` until it is validated and converted to a runnable file.
- `paper_reproduction/`: the citation, exact revision and primary-source links, author-code revision, equation/algorithm anchors, decoder status and unresolved details, plus code, circuit, noise, and reported-result identities. Keep source-specific settings and adaptation decisions here so the decoder TOML can be reused in other study settings.

The [paper index](./PAPERS.md) connects current CSS, quaternary, and circuit paper records to source targets, manifests, and assessments. The first CSS gate has three papers: [Yao BPGD](./yao-2024-guided-decimation/paper_reproduction/PAPER.md), [Bhatnagar impulse](./bhatnagar-2026-impulse-decoding/paper_reproduction/PAPER.md), and [Rabeti–Mahdavifar MBBP-LD](./rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/PAPER.md). Their 14 `.spec.toml` source records remain non-runnable. Qualified canonical adaptations are separate paper-root `.toml` files. The common parser keeps equations, references, and explanations as provenance while compiling only registered policy controls. A runnable adaptation is still `not_assessed` against the published curve.

Later source-only paper records now cover [aSCED](./wursthorn-2026-asced/paper_reproduction/PAPER.md), [Q-BP/Q-BPGD](./yao-2024-guided-decimation/paper_reproduction/PAPER.md), [MBP4](./kuo-2021-modified-bp4/paper_reproduction/PAPER.md), [Relay-BP circuits](./muller-2025-relay-bp/paper_reproduction/PAPER.md), and [BeamSearch circuits](./ye-2025-beamsearch/paper_reproduction/PAPER.md). They preserve unresolved source controls and do not imply a runnable paper-specific policy or a reproduced curve.

The [14-record qualification inventory](./qualification-v1.json) names each original CSS source revision, blocker, compiler disposition, and runnable counterpart. The selected [Yao T=100 R=2](./yao-2024-guided-decimation/bpgd-t100-r002.toml), [Bhatnagar First_Convergence/0](./bhatnagar-2026-impulse-decoding/first-convergence-0.toml), and [Rabeti MBBP-LD pilot](./rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml) use the same [bounded B1 study and command](../docs/css-literature-gate.md). Other source records remain specifications until their exact runnable mapping is qualified.

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

The public `bp-registry` command runs registered canonical CSS compositions, ordered memory/Relay, qualified Phase 5 guided-decimation and impulse interventions, the Phase 6 MBBP-LD ensemble, and the special BB72 BeamSearch/RelayBP campaign. Coordinate-majority voting has a tested kernel primitive but is rejected by the public MBBP manifest until its execution and replay contract is implemented. The four-state quaternary kernel is implemented separately; its paper-specific targets and assessments are linked in the index. A bounded Stim/Sinter CPU adapter supports plain binary flooding on independent-fault detector models, but circuit paper reproductions still require Phase 12–13 source and policy qualification. See the [researcher command guide](../docs/researcher-study-command.md) and [circuit kernel guide](../docs/circuit-kernel.md).

We will collect source statements about codes, circuits, noise, and published curves **while extracting each policy** because those details can determine the algorithm's meaning. The immutable artifacts and reproduction manifests can follow as their roadmap phases mature: CSS reproduction (Phase 9), quaternary execution/reproduction (Phases 10–11), and circuit execution/reproduction (Phases 12–13). The mapping study continues through Phase 14.
