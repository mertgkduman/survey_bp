# Literature BP policy registry

This directory collects source-grounded descriptions of BP-family decoders before their reproduction campaigns. Create one folder per **paper revision**, named `<first-author>-<year>-<short-title>`. Start from [`_paper-template/`](./_paper-template/), then add one record per decoder variant the paper defines. A variant in a paper is a source identity; it is not automatically an executable policy composition.

## Each paper folder

- `PAPER.md`: citation, exact revision and primary-source links, author-code revision if available, equations/algorithm anchors, decoder variants, unresolved details, and the source's code/circuit/noise/result identities.
- `decoders/<variant>.toml`: a **runnable** declarative file using the installed `bp-registry` policy schema. Only put a file here after its policy kinds and compatibility have passed preflight and focused equation/transition checks. Preserve the exact source basis and any adaptations in `PAPER.md`.
- `source-specs/<variant>.spec.toml`: a **mapped-only** TOML record for a decoder that cannot yet be expressed by the executable registry. Record known equations, ordering, parameters, source anchors, and unknowns. This file is research evidence, not an input to `bp-registry`.

Keep one source-specific variant per file when parameters or procedure differ materially. A controlled adaptation gets its own clearly named file and source-status entry. Do not silently fill missing parameters or equate a CSS adaptation with a circuit-paper reproduction.

## Status path

1. **Mapped only:** the paper and variant are indexed; source details and missing facts are explicit.
2. **Specified:** equations, update order, state lifetime, stopping, selection, and parameter meaning have independent source anchors.
3. **Implemented:** a compatible kernel and registered policies exist; the TOML file passes manifest preflight and focused mathematical checks.
4. **Evaluated:** a study manifest pins code/circuit, noise, seeds, budgets, expected outputs, tolerances, and denominator rules; results have a verified ledger.
5. **Reproduced or discrepant:** the prespecified statistical comparison with the paper is assessed. A runnable file alone never establishes reproduction.

The public `bp-registry` command currently runs registered canonical CSS v2/v3 compositions, schema v4 ordered memory/Relay, and the special BB72 BeamSearch/RelayBP campaign. Phase 5 intervention controls, arbitrary new policy equations, correlated quaternary inference, and circuit decoding are not generally available through that command yet. See the [researcher command guide](../docs/researcher-study-command.md).

We will collect source statements about codes, circuits, noise, and published curves **while extracting each policy** because those details can determine the algorithm's meaning. The immutable artifacts and reproduction manifests can follow as their roadmap phases mature: CSS reproduction (Phase 9), quaternary execution/reproduction (Phases 10–11), and circuit execution/reproduction (Phases 12–13). The mapping study continues through Phase 14.
