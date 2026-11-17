# Separate released Rust cores; historical derivation is unverified

The evidence supports a specific conclusion: PriorTilt does not call or depend on the RelayBP Rust crate, and its published BP kernel has a substantially different implementation. Public files and retained history do **not** prove that the authors never consulted, ported, copied and rewrote, or otherwise adapted earlier code. Those are different provenance questions.

Versions inspected:

- PriorTilt `8eefd37d694b5942fe60ec6d5c82ce97f3d2a450`, with current public manifest/core blobs checked through GitHub.
- Relay v0.2.2, `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, the existing reproduction reference.
- Current Relay main `cdfdc996ce55582c4c431f8d8392bcce57175e36`; its min-sum blob is `4a0228574b34c4fb84c6969b8c8f2e77ca2c8e97`.

| Aspect | PriorTilt | RelayBP |
|---|---|---|
| Build | Own `priortilt_rs` extension; direct dependencies PyO3, numpy and rand; no Relay package anywhere in lockfile | Separate `relay-bp`/Python-wrapper workspace |
| BP storage | Flat edge-indexed `Vec` arrays, column pointers and row-to-edge lists | Generic `MinSumBPDecoder<N>` over `SparseBipartiteGraph`, `Array1` and mapping arrays |
| Check update | Forward/backward exclusive minima using raw pointers | Minimum and second-minimum method; current main adds four independent lanes |
| Variable update | Fused raw-array prefix/suffix sums, posterior/extrema/statistics and syndrome accumulation | Graph-iterator prefix/suffix sums, with separate hard-decision and convergence routines |
| Policy | Original prior plus sparse window-statistic-driven offsets, fixed within rounds; messages continue | Gamma-weighted prior/posterior memory and repeated relay legs |
| Precision/configuration | Macro-generated f64/f32 cores specialized for PriorTilt | Generic numeric decoder, memory/scaling/bounding/fixed-point options |

Primary code:

- [PriorTilt manifest](https://github.com/ionq-publications/PriorTiltDecoder/blob/8eefd37d694b5942fe60ec6d5c82ce97f3d2a450/decoder/Cargo.toml)
- [PriorTilt fields](https://github.com/ionq-publications/PriorTiltDecoder/blob/8eefd37d694b5942fe60ec6d5c82ce97f3d2a450/decoder/src/lib.rs#L92-L129), [BP iteration](https://github.com/ionq-publications/PriorTiltDecoder/blob/8eefd37d694b5942fe60ec6d5c82ce97f3d2a450/decoder/src/lib.rs#L213-L326)
- [Pinned Relay fields](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs#L76-L92), [check update](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs#L332-L395), [variable update](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs#L406-L476)
- [Relay current check update](https://github.com/trmue/relay/blob/cdfdc996ce55582c4c431f8d8392bcce57175e36/crates/relay_bp/src/bp/min_sum.rs), [relay controller](https://github.com/trmue/relay/blob/cdfdc996ce55582c4c431f8d8392bcce57175e36/crates/relay_bp/src/bp/relay.rs#L74-L85)

Both implement the ordinary min-sum BP equations. Common prefix/suffix variable-node accumulation, Rust/PyO3/NumPy bindings and a standard observable-prediction interface are not sufficient evidence of source copying. The different check-update/data representations are implementation differences, not different definitions of min-sum mathematics.

The public PriorTilt history starts with a complete flat-array implementation in `f7e209bb72f019013bd6802b46f39221d136d6e6`; only one subsequent commit changes this Rust file. The initial source includes an unspecified reference to C++ arithmetic. It does not identify the referenced implementation and does not establish a Relay provenance link. The README's "from scratch" section concerns re-simulating the experiments; it is **not** an explicit clean-room authorship declaration. License/copyright headers and the absence of a preserved fork history likewise do not prove independent origin.

The earlier observable-only scoring result is not evidence of common Rust code: Relay's own observable runner also offers a plain observable projection and a separate detailed convergence result, which is natural for the Sinter interface. This does not settle implementation lineage.

No performance benchmark, algorithm, campaign, source checkout or reproduction reference was changed. Static evidence assertions and version/manifest inspection are in `check.py`/`evidence.json`. Stronger historical claims would require an author statement or identifiable source-transfer history.
