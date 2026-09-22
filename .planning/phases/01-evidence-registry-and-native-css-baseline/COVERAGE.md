# API Coverage — Phase 1 native CSS dependencies

> Full coverage is the starting point. Each excluded capability has a reason. This matrix covers the external SDK surfaces Phase 1 actually binds: `ldpc==2.4.1` `BpDecoder` for the native binary BP reference and `bposd==2.1` `css_code` for frozen logical-operator extraction. It does not claim integration of the packages' other classes.

The decisions are for the Phase 1 CSS code-capacity pilot. `INTEGRATE` means the capability is called or read by the implementation and checked in the native smoke or source-artifact tests. Future phases must revisit opt-outs before expanding the reference or canonical decoder. The native adapter remains a pilot adaptation, not a source-faithful BPGD or impulse implementation.

| capability | decision | reason |
|---|---|---|
| `ldpc.BpDecoder` binary check matrix constructor | INTEGRATE | |
| `ldpc.BpDecoder.error_rate` uniform prior | INTEGRATE | |
| `ldpc.BpDecoder.max_iter` explicit iteration budget | INTEGRATE | |
| `ldpc.BpDecoder.bp_method=product_sum` | INTEGRATE | |
| `ldpc.BpDecoder.schedule=parallel` | INTEGRATE | |
| `ldpc.BpDecoder.input_vector_type=syndrome` | INTEGRATE | |
| `ldpc.BpDecoder.decode(syndrome)` candidate | INTEGRATE | |
| `ldpc.BpDecoder.converge` and `iter` status | INTEGRATE | |
| `ldpc.BpDecoder.error_channel` per-bit prior | OPT-OUT | Phase 1 uses an X-only uniform bit-flip channel. |
| `ldpc.BpDecoder.bp_method=minimum_sum` and `ms_scaling_factor` | OPT-OUT | Alternative BP update rules belong to later policy-family work. |
| `ldpc.BpDecoder.schedule=serial` and `serial_relative` | OPT-OUT | Phase 1 pins flooding for the native baseline; schedule comparisons come later. |
| `ldpc.BpDecoder` serial ordering and randomization options | OPT-OUT | These configure serial schedules excluded from the Phase 1 baseline. |
| `ldpc.BpDecoder.omp_thread_count` control | OPT-OUT | Phase 1 controls OpenMP through the recorded run environment and does not expose this constructor option. |
| `ldpc.BpDecoder.input_vector_type=received_vector` or `auto` | OPT-OUT | The CSS reference receives an explicit syndrome, including for square checks. |
| `ldpc.BpDecoder.update_channel_probs` and mutable `channel_probs` | OPT-OUT | The pilot uses a fixed prior for each shot; dynamic priors require separate semantics. |
| `ldpc.BpDecoder.log_prob_ratios`, `decoding`, and other decoder state inspection | OPT-OUT | The native API is used as a black-box reference; internal state is not part of the Phase 1 evidence contract. |
| `ldpc.BpDecoder` edge-update counters | OPT-OUT | The installed class exposes no such counter; the ledger records null with a reason. |
| `bposd.css.css_code(hx, hz)` construction | INTEGRATE | |
| `bposd.css.css_code.K`, `lx`, and `lz` logical output | INTEGRATE | |
| `bposd` decoder and OSD execution APIs | OPT-OUT | `bposd` is only a source-artifact logical provider in Phase 1; optional postprocessing is later work. |

The `ldpc` list follows the installed `BpDecoder.__doc__` and public attributes observed on the development node; the implemented boundary is [`reference.py`](../../../src/bp_registry/reference.py). The `bposd` boundary is [`freeze_css_source.py`](../../../tools/freeze_css_source.py). Version and node observations are recorded in [`environment-pins.md`](../../../docs/environment-pins.md).
