# BB72 CSS BeamSearch and RelayBP parameter campaign

This campaign extends the eight-shot implementation fixture with independent parameter selection and evaluation. It is a controlled BB72 X-only CSS code-capacity comparison. The [BeamSearch](https://arxiv.org/html/2512.07057v2) and [RelayBP](https://arxiv.org/html/2506.01779v2) papers use circuit-level settings; this campaign does not reproduce their reported curves.

## Frozen design

The [machine-readable design](../data/studies/fair-beam-relay-css-v2.json) fixes p=0.05 and p=0.08. Each rate gets 128 parameter-selection shots and a disjoint evaluation cohort of 512 or 1,280 shots, respectively. Three profiles allow 5, 10, or 20 BP iterations per extra unit. All profiles use the same 20-iteration initial min-sum BP, V2C fresh-message coefficients 1.0 and 0.5, and 8,640 additional C2V updates at most. BeamSearch uses width 2 and at most four branching rounds; RelayBP may use up to eight disordered-memory legs. These are topology limits, not equal-work claims.

Within a rate and cohort, every profile and damping arm sees the same physical sample identities. Each profile shares its exact initial BP object between BeamSearch and RelayBP. The selection rule minimizes unconditional failures separately for each rate, damping, and method; ties use total C2V updates and then profile ID. `selection-lock.json` fixes that choice before evaluation files are allowed. Evaluation runs the full grid but applies four predeclared selected Beam-versus-Relay paired contrasts with Holm correction. All other settings remain descriptive.

Each shard has a frozen manifest, shot ledger, result hash, source seal, and deterministic replay gate. Observed serial runtimes are descriptive. The decoded candidate is judged on the original CSS problem after decoder execution, using the hidden physical error only at the evaluator boundary. Every terminal shot remains in the denominator.

## Run

From the repository root, first prepare a source-sealed output:

```bash
.venv/bin/python scripts/run_fair_beam_relay_campaign.py prepare \
  --design data/studies/fair-beam-relay-css-v2.json \
  --output data/results/fair-beam-relay-css-v2
```

Run the six `selection` rate/profile shards, then `select`; run the six `evaluation` shards, then `report`. `scripts/run_fair_beam_relay_campaign_slurm.sh` maps Slurm array indices 0–5 to the six shards and uses eight independent shot workers per shard (48 cores if all six array tasks run together). Numerical libraries remain single-threaded per worker. The runner's `verify` command replays a single shard. The final `report` command replays all evaluation shards and writes `result.json`, `REPORT.md`, and `study.html`. No results are publication-qualified until all checks pass.
