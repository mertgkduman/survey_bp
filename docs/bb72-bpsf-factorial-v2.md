# Independent BB72 BP-SF factorial v2

The [frozen design](../data/studies/bb72-bpsf-factorial-v2.json) follows the published [BB72 CSS BP v1 comparison](../data/results/bb72-css-bp-v1/REPORT.md) with a new physical-sample namespace. The v1 (p=0.08) comparison found 20 BP-SF gains and four losses against undamped SPA in 512 matched shots. The [independent ledger audit](evidence/bb72-v1-bpsf-audit.json) confirms those counts: 18 gains followed SPA's iteration cap, while BP-SF converted many unavailable outputs into syndrome-valid candidates, including some logical failures. V1 did not record intervention decode runtime. The v1 result is a hypothesis source and is never pooled into v2 inference.

## Fixed arms and comparisons

Each rate has 12 configurations: canonical SPA or min-sum updates, fresh-message weight γ of 1 or 0.5, and one of three modes. `bp20` stops plain BP after at most 20 flooding sweeps; `bp40` permits 40; `bpsf20plus4x5` runs 20 baseline sweeps followed by at most four five-sweep syndrome-flip tests. Every arm has the same 8,640 C2V and V2C message caps per shot. All other admitted work is preserved in its typed vector. The BP20 control shows what is gained by using a 20-sweep starting point; BP40 is the equal message-envelope reference for each intervention contrast.

The [BP-SF paper](https://arxiv.org/html/2507.00254v1) uses min-sum and parallel speculative tests. Both canonical BP-SF arms here use deterministic seeded, serial first-valid test selection, so the min-sum arm is source-informed but remains an adaptation. The source [damping equation](https://arxiv.org/html/2411.08177v2#S4.SS2) was studied on erasures. Our γ=0.5 bit-flip use is a controlled transplant. The pinned Bravyi BB72 artifact comes from the [author repository](https://github.com/sbravyi/BivariateBicycleCodes/tree/fa77e3333d3ec44c79d8f914dd24c040d1da471b); its circuit-level BP-OSD experiment is outside this perfect-syndrome CSS study.

At (p=0.08), the two prespecified primary paired contrasts are BP-SF versus BP40 for undamped SPA and undamped min-sum. Each uses 1,280 new matched physical samples. They use two-sided exact McNemar tests and Holm adjustment across this two-contrast family. Directional claims require adjusted (p\leq 0.05) and the matching observed sign. The 512 new matched (p=0.05) samples, γ=0.5 arms, and BP20 controls are descriptive; their exact marginal intervals and paired discordances are retained without unadjusted superiority claims. All terminal shots count, including no output and logical failure.

The 1,280-shot primary denominator was chosen before sampling. A sensitivity calculation with discordance probability 0.05, a two-percentage-point absolute difference, and conservative two-sided α=0.025 gives approximately 81.8% power under that *assumed* scenario. The assumption is uncertain, especially for min-sum. A smaller effect may remain inconclusive; no adaptive extension is permitted within this design.

## Cost and evidence

The report presents failure fractions, exact 95% binomial intervals, matched gains/losses, BP messages and calls, all additional typed intervention work, and per-shot runtime availability. BP-only and intervention runtime have different scopes. BP-SF runtime covers its serial controller, including branch setup; BP-only decode runtime excludes part of setup. Reported runtime is a same-node descriptive observation, not normalized parallel latency or a source speed claim. A common message cap does not equate all non-message work.

The study runner validates all 24 manifests before shots, seals the design and implementation hashes, and verifies every public ledger before reporting. A changed seal, missing terminal, altered ledger, mismatched physical sample, or v1 sample identity blocks the report. Outputs are under `data/results/bb72-bpsf-factorial-v2/`. The offline HTML and deterministic compressed-ledger package are generated only after report verification.

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py preflight
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py run --workers 24
OMP_NUM_THREADS=1 BB72_V2_VERIFY_WORKERS=12 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py report
.venv/bin/python scripts/render_bb72_bpsf_factorial_v2.py
.venv/bin/python scripts/package_bb72_bpsf_factorial_v2.py
```

Use bounded Slurm allocations for production. The GitHub publication helper checks package digests and stages only the verified compressed package; uncompressed ledgers and operational logs remain on the HPC filesystem.
