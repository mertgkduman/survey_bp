---
spike: '060'
idea: priortilt-figure1
name: priortilt-figure1-campaign
type: standard
verdict: PARTIAL
related: ['057']
tags: [circuit, priortilt, figure1]
---

# One-CPU source-grid circuit campaign

User-authorized scope: review project goals and reproduce Fig1 with canonical BP-family decoders, one CPU per point. Source and mathematical qualification precede production dispatch. Preserve prior evidence and phase gates.

## Research

Primary paper: https://arxiv.org/html/2611.13373v1
Author artifact repository: https://github.com/ionq-publications/PriorTiltDecoder

## Investigation Trail

Initial source review finds exact circuit artifacts, raw Fig1 measurements and optimized three-phase parameters available. Circuit memory is evaluated through detector/observable semantics rather than a CSS code-capacity substitute. PriorTilt is 60+3000x6 sweeps, RelayBP-1 is 80+300x60, and beam32_340iters is width32 with40 initial and10x30 continuation sweeps per path. The figure metric is (X-memory errors/shots + Z-memory errors/shots)/cycles.

## Results

Source/controller qualification passed; production was submitted and is not yet complete.

## Frozen production launch

Source and mathematical qualification passed before dispatch. The final affected regression run passes348 tests; source/native checks cover72 PriorTilt+72 Beam/Relay controller cases and144 ordinary-BP numerical-order probes, plus624 independent full-budget circuit pilot events. A paired-memory recovery test caught and fixed a JSON tuple/list manifest mismatch before freezing. Tests cover exact failure prefixes, zero-error bounds, shared noise across methods, committed versus uncommitted crash output, stale/tampered sample/work receipts, independent logical failure versus nonconvergence, and audited-only/empty publication.

Frozen study: `data/reproductions/priortilt-2611-13373/plan.json`, SHA256 `3e466081790d913ae2fb0a477f654bd0218504a79e7d969b989b62043b7e829c`. All39 plotted points are thirteen code/rate combinations ×three methods. Every worker handles its X/Z memories sequentially/interleaved on **one CPU**,3GiB, with four-day walltime/requeue, private JIT caches, thread limits1, shared immutable packed samples and atomic columnar event chunks. The array is **61946754** (tasks0–38); all39 were observed RUNNING with CPUs1. Collector **61946755** is dependency-queued; Slurm allocates two CPUs for its12GiB request, which is a reporting job rather than a point simulation. Worker audits run in fresh Python interpreters within the same one-CPU allocations. Raw observations/candidates/path ledgers remain under ignored `results/` without deletion.

Local stopping is20 observable errors or100M decoded shots **per memory basis**, separately from the authors' larger precision. Paper metric, denominator and canonical/nonnative numeric differences remain explicit. Publish only a fully completed, audited X/Z pair, with summed component uncertainty; do not publish unfinished-shot provisional bounds. A source-only initial report/three-panel figure was generated and inspected with0/39 local points. The collector rehashes receipts, complete ledgers and samples before reporting.

Existing raw results, historical manifests and kernels, old jobs, public catalog/v1 and configured models are unchanged. No simulations from earlier studies were rerun and no phase gates/counters moved. The outstanding production task is to let the39 points finish, audit them, then assess each paper ordinate against its local interval. Future public catalog integration must represent paired-memory inputs and the figure metric honestly, not invent a single Stim circuit or pooled binomial denominator.

Evidence: [launch verification](verification.json), [dispatch commands/IDs](../../../data/reproductions/priortilt-2611-13373/dispatch.json), [campaign guide](../../../data/reproductions/priortilt-2611-13373/README.md), and [audited result report](../../../data/reproductions/priortilt-2611-13373/RESULTS.md).

Verdict: PARTIAL — implementation, freeze, qualification and one-CPU dispatch are complete; statistical reproduction remains running, with no source agreement claim yet.
