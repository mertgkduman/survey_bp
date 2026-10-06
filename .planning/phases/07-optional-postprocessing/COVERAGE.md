# Phase 7 External API Coverage

Phase 7 integrates one released external SDK (`ldpc==2.4.1`) and one source-pinned optional build. All other SI/OTF mechanics use project-owned code against pinned primary-source semantics. This matrix is the API-coverage gate for planning and execution.

> Full coverage by default. Opt-outs are explicit, reasoned decisions.

| capability | decision | reason |
|---|---|---|
| ldpc 2.4.1 standalone LSD | INTEGRATE | |
| ldpc 2.4.1 native BP-OSD composite | INTEGRATE | |
| ldpc 2.4.1 native BP-LSD composite | INTEGRATE | |
| official standalone OSD commit baec4c8 | INTEGRATE | |
| BPOTF runtime SDK/build | OPT-OUT | Phase 7 uses the pinned repository as an algorithm/source reference for a project-owned binary-CSS adaptation; faithful circuit runtime integration belongs to Phases 12–13. |

## Contract detail

| External surface | Exact identity | Phase 7 use | Contract coverage | Failure / drift coverage | Planned evidence |
|---|---|---|---|---|---|
| `ldpc.lsd_decoder.LsdDecoder` | released `ldpc==2.4.1`, official commit `d3429964cd4ffe1abfc041c6ec8b8425cb174f40` | Canonical BP handoff to standalone LSD | Constructor `pcm`, `bits_per_step=1`, `lsd_order`, `lsd_method`; `decode(syndrome, bit_weights)`; `LSD_0`, `LSD_E`, `LSD_CS`; finite shape/sign/order checks | Wrong version/import, bad enum/order, nonfinite/wrong-length input, equal-weight tie behavior, malformed/invalid output, opaque counter missingness | 07-01; `tests/canonical/test_postprocessing_lsd.py` |
| `ldpc.BpOsdDecoder` | released `ldpc==2.4.1`, official commit above | Distinct native composite reference | Explicit BP controls plus `osd_method`, `osd_order`; native convergence/final output and exposed iterations | Wrong package/API, constructor drift, native error/nonconvergence, invalid output, internal-work unavailable reasons, canonical/native identity collision | 07-06; `tests/test_reference_smoke.py` |
| `ldpc.BpLsdDecoder` | released `ldpc==2.4.1`, official commit above | Distinct native composite reference | Explicit BP controls plus `bits_per_step`, `lsd_order`, `lsd_method`, `always_run_lsd`; legacy aliases rejected from manifests | Wrong package/API, implicit alias/default, native error/nonconvergence, invalid output, internal-work unavailable reasons | 07-06; `tests/test_reference_smoke.py` |
| standalone `OsdDecoder` | official `quantumgizmos/ldpc` `standalone_osd` commit `baec4c8bfa2a679b0ba0e72df5582e277cd6918b` | Canonical BP handoff to OSD through isolated process | Blocking-human legitimacy approval; exact clone/build/wheel/environment/import/constructor/method receipt; strict worker request/response; OSD0/exhaustive/combination fixtures | Moving source, build/import/API drift, primary environment mutation, receipt tamper, worker timeout/error, rank deficiency, equal weights, invalid output | 07-02/07-03; `data/qualifications/phase7-standalone-osd-baec4c8.json`; `tests/canonical/test_postprocessing_osd.py` |
| BPOTF repository | official commit `da6caa4509dadb8620d8cac38108b4816897b18b` | Algorithm/source reference only; no runtime SDK or package integration | Source/code identity and known TODOs retained; Phase 7 implements a separately named project-owned binary-CSS adaptation | Any runtime import/build claim is rejected; circuit fidelity remains non-runnable/deferred | 07-05/07-08; `tests/canonical/test_postprocessing_otf.py` and OTF source/adaptation TOMLs |

## Gate decisions

- No new registry package is installed in the primary `.venv`.
- The standalone OSD source build is the only new executable dependency action and cannot start until Plan 07-02 records blocking-human approval.
- The isolated OSD worker is selected by a committed qualification digest, never by a manifest-supplied module or shell path.
- Native composites retain their internal BP and are reference arms. Canonical OSD/LSD consume only a frozen canonical-BP handoff.
- External outputs are binary/shape/finiteness checked and independently validated against the immutable original problem before eligibility or evaluation.
