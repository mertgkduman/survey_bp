---
status: passed
scope: campaign_setup_and_dispatch
campaign_status: tuning_running
confirmation_status: pending
---

# Verified Roffe damping campaign setup and live dispatch

- Separate frozen 1,526-point training plan uses seven damping values, 1,024 fixed paired shots per source rate, four original toric codes and T=n (162/242/338/450). The original 218-point Roffe plan retains SHA256 `eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3` and all active MacKay plans still load.
- Both binary and joint-Pauli min-sum damping independently satisfy d*old+(1-d)*fresh at each tested alpha_t; sample identities and exact directed-work counters pass. No canonical, shared-runtime, archived-v1 or previous scientific file changed.
- Selection handles unequal 25/28-point grids, rejects missing/unpaired data, prioritizes LER over speed, and reuses the tested simultaneous paired-regret guard. Fresh confirmation preserves source grids and T=n, seed separation, zero-damping controls, one CPU per point and 20-failure/1e8-shot stops. Duplicate zero-damping arms are suppressed.
- Dispatch lock, persisted receipts, afterok continuation and recovery without a duplicate array pass. Actual Slurm test-only validation passed. Real array61789908 and dependent controller61789909 were accepted; workers started and terminal jobs exited0:0. Real production terminal ledgers for both binary BP and Q-BP passed full work/count/manifest verification and endpoint replay. Snapshot at00:11 UTC:234/1526 terminal points,175 running, no launch errors.
- 90 tests passed:11 new damping,39 prior study/dispatch/controls,40 catalog/projection.16 Chromium workflow groups passed:7 actual public results,5 original Roffe and4 future damping overlays. CSV/settings, both work metrics, source-specific changing scale, saved settings, empty results/custom inputs and stale hidden choices pass with no browser errors.
- A separate unregistered qualification experiment retained16 real damped min-sum shots across binary/Q-BP. Both full ledgers, endpoint replays, exact resume and held-out publication normalization passed. These qualification shots do not enter training or confirmation.
- Empty confirmation extension leaves88 curves/637 points/12 codes/0 registered circuits. All165 retained raw series and all code records remain equal. Existing tracked Roffe evidence links now resolve publicly.

New training plan SHA256: `35ae5a9eb0bbe6c0cb8d78276708c61718d5435809efe108b589551a2c574104`. Scheduler and validation snapshots are in `launch-status.json` and `validation.json`.

This verifies setup and actual execution. Damping selection, independent confirmation, final full audit and result publication are pending automatic stages; no scientific outcome or completed production campaign is claimed.
