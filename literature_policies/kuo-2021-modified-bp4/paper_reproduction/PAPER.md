# Kuo and Lai MBP4 source record

- Primary source: [arXiv:2104.13659](https://arxiv.org/pdf/2104.13659), pinned PDF SHA-256 `37d3a734c1e617eecc45ed1cd641dd92b89adfd7e15390ef403d90637c547f23`.
- Requested source policy variants: [α=1 mechanism](../mbp4-alpha1-mechanism.spec.toml) and [α=1.5 mechanism](../mbp4-alpha15-mechanism.spec.toml). Both preserve the Figures 8–9 five-qubit parallel, β=0 mechanism setting and remain non-runnable source records.
- Source target and manifest: [Figures 8–9 target](../../../data/source-targets/phase11-mbp4-figures8-9-five-qubit.json), [mechanism manifest](../../../data/manifests/phase11-mbp4-figures8-9-five-qubit.json).
- Assessment: [deterministic mechanism only](../../../data/results/phase11-mbp4-figures8-9/assessment.json). It does not assess a curve or rank decoders.
- Figure 6 α=1.5 statistical target: [review candidate](../../../data/source-targets/phase11-mbp4-curve-review.json) and [blocked policy record](../../../data/source-targets/phase11-mbp4-curve.json). Its physical coordinates, intervals, iteration cap, denominator, stopping, uncertainty, tolerance, resources, β/schedule/numerical details, and author implementation identity remain unresolved. The Figures 8–9 mechanism settings are not silently reused for that curve.
