# Relay-BP circuit source record

- Paper revision: [arXiv:2506.01779v2](https://arxiv.org/html/2506.01779v2).
- Author implementation: [trmue/relay v0.2.2](https://github.com/trmue/relay/tree/v0.2.2), pinned at `14cb31a18f9b9d7d099791b793e35b8a2951f8f3` in the [native receipt](../../../data/evidence/relay-v0.2.2-source.json).
- Source circuit inventory: [672 byte-verified Stim fixtures](../../../data/circuits/relay-v0.2.2/README.md), including bivariate bicycle, color, and surface memory circuits.
- Policy record: [`relay-bp-circuit.spec.toml`](../relay-bp-circuit.spec.toml), non-runnable. The current [circuit CPU adapter](../../../docs/circuit-kernel.md) supports plain flooding SPA/min-sum, not source Relay memory and state transfer.
- Reproduction state: circuit-paper target, exact decoder settings, circuit/DEM extraction, source numerical profile, stopping, and native/canonical transition agreement are not qualified. The [author-release bounded profile](../../../reports/circuit-bp-cpu-profile-author-v022.json) uses the same observations and graph for plain min-sum throughput only; it is not paper-curve evidence.
