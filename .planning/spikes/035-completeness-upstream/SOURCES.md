# Upstream correspondence, checked 2026-11-08

| Reference | What was checked | Correspondence and limits |
|---|---|---|
| [Kschischang–Frey–Loeliger, sum-product](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf) | Factor-local extrinsic updates and tree marginals | Independent enumeration is the mathematical acceptance criterion; loopy covariance and native agreement are separate checks. Neither implies MAP or optimal quantum coset decoding. |
| [ldpc BP documentation](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) | Per-bit channel input, SPA/MS, parallel/serial schedules, explicit input interpretation | 216 new heterogeneous-prior DEM cases execute installed native SPA/MS, matching candidates, convergence and iteration counts. The installed binary is hashed in results; its build commit is not established. Uniform compiled CSS binding is narrower than this channel interface. |
| [Sionna 2.2.0 LDPCBPDecoder](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) | Callable CN/VN updates, ordered message callbacks, custom CN schedules, returned state and clipping | Architectural comparison only. Canonical scalar hooks support some analogous extensions, while compiled dispatch is a closed policy set. No Sionna execution, training equivalence or new numerical comparison is claimed. Earlier 2.1.0 phi transcriptions remain frozen in spike 028. |
| [Stim DEM specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md) | Independent error instructions, detector/observable XOR effects and decomposition separators | Exact small affine-projection fixture includes p=0, p=1, separator-linked effects and an undetected logical fault. This does not prove a circuit noise process with correlated mechanisms is losslessly approximated by an arbitrary DEM. URL is mutable main; this is a documentation check, not a pinned executable reference. |
| [Relay pinned min-sum](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) | Prior executable inner-memory correspondence | Reused source-hashed receipt from spike 033; no new full-controller or published-curve claim. |
| [aSCED pinned SPA source](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp) | Prior source-specific zero-message classification | Reused source-hashed receipt from spike 033; exact author splitter/ensemble reproduction is a separate Phase 11 question. |
| [BP+OSD repository](https://github.com/quantumgizmos/bp_osd) | Position of optional postprocessing relative to BP | Scope reference only. BP-internal behavior remains the priority; OSD/LSD success cannot validate BP equations or cure an admitted policy mismatch. |

## Approach comparison

| Approach | Strength | Limitation | Use here |
|---|---|---|---|
| Independent probability enumeration | Detects shared implementation errors | Exponential cost; tree exactness needs a compatible schedule and no approximation | Primary mathematical acceptance on small fixtures |
| Aligned native execution | Tests practical conventions and stopping | Native implementations can share errors or use intentional approximations | Executed ldpc comparisons plus retained pinned controls |
| Source/API comparison | Reveals extension and representation gaps | Does not establish runtime parity | Sionna interfaces and Stim semantics |

No repository is treated as a universal gold standard. The acceptance contract separates mathematics, finite precision, control flow, candidate evaluation, provenance and performance.
