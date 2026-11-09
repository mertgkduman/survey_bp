# Active v2 removals

Before/after refer to the active projected evidence and public input lists, not deletion of retained records. Each removed curve has exactly one measured rate.

| Item | Before | After | Removed |
|---|---:|---:|---:|
| curves | 105 | 63 | 42 |
| points | 361 | 319 | 42 |
| codes | 7 | 6 | 1 |
| circuits | 3 | 0 | 3 |

The projected point totals also equal the sum of distinct rates per curve in this snapshot.

Hidden code: gb46 (GB46; no displayed result).

Hidden registered circuits: relay-surface-d3 (RelayBP rotated surface-code d=3 memory X); relay-bb144-memory-z (RelayBP BB144 memory Z); beamsearch-bb144-memory-z-p005 (BeamSearch BB144 memory Z p=0.005).

The three-qubit fixture was already absent from public catalog/examples; the active view now also excludes both registered aliases if imported. Internal fixture/backend and archived v1 references are intentionally preserved.

| Input | Dataset(s) | Removed curve | Rate | Curve ID |
|---|---|---|---:|---|
| bb72 | bb72-fair-beam-relay-v2 | BeamSearch, γ = 1, I₀ = 20, I₊ = 5, w = 2, R = 4, noise = X-only, precision = float64 | 0.08 | curve-d86b0b9f |
| bb72 | bb72-fair-beam-relay-v2 | BeamSearch, γ = 1, I₀ = 20, I₊ = 10, w = 2, R = 4, noise = X-only, precision = float64 | 0.05 | curve-9ae37d4d |
| beamsearch-bb144-memory-z-p005 | circuit-cpu-profile-beamsearch | Detector BP, MS, T = 8, precision = float64 | 0.005 | curve-245ea4d5 |
| relay-bb144-memory-z | circuit-cpu-profile-relay | Detector BP, MS, T = 8, precision = float64 | 0.005 | curve-ac18d25f |
| relay-surface-d3 | circuit-cpu-profile-relay | Detector BP, MS, T = 8, precision = float64 | 0.005 | curve-76a554ec |
| double-gross | pfister-presentation-full-v2-curves | Q-BP, SP, d = 0.1, c = none, T = 1000, p₀ = p, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-9d05175 |
| a5 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0.2, c = none, T = 10000, p₀ = 0.005, noise = depolarizing, precision = float64 | 0.06 | curve-eea87e2e |
| a5 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0.2, c = none, T = 100, p₀ = 0.005, noise = depolarizing, precision = float64 | 0.06 | curve-9c9df4be |
| a5 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0, c = none, T = 100, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-efe2cff1 |
| a5 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0, c = none, T = 3000, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-919dc80b |
| b2 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0.1, c = none, T = 5000, p₀ = 0.15, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-35229bdc |
| b2 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0.1, c = none, T = 100, p₀ = 0.15, noise = depolarizing, precision = float64 | 0.06 | curve-20044b6e |
| b2 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0, c = none, T = 100, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-74da7aff |
| b2 | yao-bp4-tuning-fairness-p006 | Q-BP, SP, d = 0, c = none, T = 2400, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-49de055f |
| a5 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 10000, p₀ = 0.045, noise = depolarizing, precision = float64 | 0.06 | curve-49095aec |
| a5 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 10000, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-a142e903 |
| a5 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 10000, p₀ = 0.075, noise = depolarizing, precision = float64 | 0.06 | curve-3fea7f8f |
| a5 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.2, c = none, T = 10000, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-801de430 |
| a5 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.3, c = none, T = 10000, p₀ = 0.06, noise = depolarizing, precision = float64 | 0.06 | curve-c1d3f5b5 |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.05, c = none, T = 5000, p₀ = 0.15, noise = depolarizing, precision = float64 | 0.06 | curve-ec11bd23 |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.15, c = none, T = 5000, p₀ = 0.15, noise = depolarizing, precision = float64 | 0.06 | curve-6579944 |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 5000, p₀ = 0.14, noise = depolarizing, precision = float64 | 0.06 | curve-4a94853a |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 5000, p₀ = 0.15, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-6b7a8e27 |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 5000, p₀ = 0.16, noise = depolarizing, precision = float64 | 0.06 | curve-5a96b1d4 |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.1, c = none, T = 5000, p₀ = 0.18, noise = depolarizing, precision = float64 | 0.06 | curve-9eab7a5e |
| b2 | yao-bp4-tuning-selected-validation | Q-BP, SP, d = 0.2, c = none, T = 5000, p₀ = 0.15, noise = depolarizing, precision = float64 | 0.06 | curve-11608638 |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 100, R = n, order = random, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-a10ed677 |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 100, R = n, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, pilot | 0.04 | curve-b546d989 |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 100, R = 10, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-b71d7687 |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 100, R = 882, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, pilot | 0.04 | curve-b1908e55 |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 10, R = n, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-8dbe669e |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 1, R = n, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-4465a78c |
| b1 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 70, R = n, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-f3b4c478 |
| c2 | yao-non-osd-results | BPGD, SP, d = 0, Tᵣ = 10, R = n, cᵥ = 25, p₀ = p, noise = X-only, precision = float64, importance-weighted estimate | 0.04 | curve-bf3b9c82 |
| a5 | yao-tuned-qbpgd-p006 | Q-BPGD, SP, d = 0, c = none, p₀ = 0.06, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-12932e58 |
| a5 | yao-tuned-qbpgd-p006 | Q-BPGD, SP, d = 0.2, c = none, p₀ = 0.005, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-251c85a0 |
| b2 | yao-tuned-qbpgd-p006 | Q-BPGD, SP, d = 0, c = none, p₀ = 0.06, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-e486699a |
| b2 | yao-tuned-qbpgd-p006 | Q-BPGD, SP, d = 0.1, c = none, p₀ = 0.15, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, separate evidence | 0.06 | curve-ba20703a |
| a5 | yao-tuned-qbpgd-p006-pilot-n1000 | Q-BPGD, SP, d = 0, c = none, p₀ = 0.06, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, pilot | 0.06 | curve-6b4186c5 |
| a5 | yao-tuned-qbpgd-p006-pilot-n1000 | Q-BPGD, SP, d = 0.2, c = none, p₀ = 0.005, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, pilot | 0.06 | curve-707bcdd |
| b2 | yao-tuned-qbpgd-p006-pilot-n1000 | Q-BPGD, SP, d = 0, c = none, p₀ = 0.06, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, pilot | 0.06 | curve-ffe3527b |
| b2 | yao-tuned-qbpgd-p006-pilot-n1000 | Q-BPGD, SP, d = 0.1, c = none, p₀ = 0.15, Tᵣ = 10, R = n, ε = 1e-10, noise = depolarizing, precision = float64, pilot | 0.06 | curve-1be48a1b |
