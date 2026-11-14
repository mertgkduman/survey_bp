# Roffe Figure 3: tuned damped min-sum BP and Q-BP

Controlled extension of the completed Roffe 2020 Figure 3 campaign. The frozen original plan, raw evidence, source ordinates, matrices and kernels remain unchanged. No OSD executes.

Each toric code uses its own paper rate grid: [[162,2,9]] has 25 rates, [[242,2,11]], [[338,2,13]] and [[450,2,15]] have 28 each. Ordinary binary BP uses X-only noise at p_X. Joint quaternary Q-BP uses depolarizing p=1.5*p_X and matched joint priors: this is a different channel, so differences cannot be attributed to Q-BP alone. Both execute canonical flooding min-sum, alpha_t=1-2^-t beginning at t=1, float64, fixed p prior, no cap and no zero-syndrome shortcut. Maximum sweeps are the paper's T=n (162/242/338/450) at every stage.

## Prospective tuning and selection

Damping d is the old V2C-message weight: new=d*old+(1-d)*fresh, applied by the existing canonical policy. Test d={0,.1,.3,.5,.7,.85,.95}. Each candidate/rate executes exactly 1,024 shots (failure target 1,025), seed 2026111411. The sampler excludes damping from its physical-sample identity; full physical hashes are compared before selection. There are 1,526 points and 1,562,624 training decoder shots. Training results never enter the public results catalog or confirmation denominators.

Choose one damping per code/family, minimizing mean block LER over that code's equally weighted source rates. Logical failures include nonconvergence and either nontrivial logical residual. Only candidates whose simultaneous paired risk-regret upper bound is within 10% of empirical-best mean LER can compete on mean executed iterations. There is no positive absolute similarity floor. Exact discordance tails are Bonferroni-corrected over both tails, every ordered candidate/reference pair and all 218 code/family/rate strata (including unequal 25/28 grids). This reuses the qualified MacKay selector unchanged. Overlapping marginal intervals do not establish equivalence. If zero damping wins, preserve it honestly rather than force a positive value. Selection remains provisional until independently evaluated.

## Independent confirmation

After a complete ledger/count/work/endpoint-replay audit, freeze selection.json and a second plan. Confirm selected damping and d=0 for every code/family on seed 2026111413, at every original rate, stopping at 20 block failures or 100,000,000 shots. Selected/baseline share the fresh physical stream, but may retain different prefix lengths because of failure stopping. If selected d=0, execute it once. Between 218 and 436 confirmation points result. Report stopping-aware intervals, mean iterations and mean directed edge updates per shot, with raw ledgers retained. No tuned-decoder superiority or simultaneous agreement claim is prespecified by a 20-failure confirmation.

Only audited confirmation evidence is registered for display. The public catalog remains empty for this extension until confirmed multi-rate results exist. Original source ordinates remain in the undamped source campaign; modified-policy curves do not relabel those ordinates as their own paper results.

## Execution

```sh
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-damping/run.py --freeze
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-damping/run.py --test-only
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-damping/run.py --submit
```

One CPU and 2 GiB per point; native threads=1; maximum array concurrency392. Preflight: MaxArraySize50001, association400 CPUs/1500000M, existing jobs6 CPUs/12GiB, original Roffe maximum RSS138.2MiB. Arrays fit the measured limits. Locks and persisted scheduler receipts prevent duplicate dispatch. afterok continuations require complete audits before selecting, freezing and submitting confirmation; final continuation audits and refreshes the catalog. No subsequent paper is dispatched. Reusing --submit repairs a missing continuation without duplicating an existing array. Failed jobs remain visible and prevent dependent publication.
