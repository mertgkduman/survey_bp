# BP4 equal-cap and mean-work controls at physical p=0.06

This is a controlled follow-up to the [A5/B2 BP4 tuning study](../README.md).
The earlier tuned-versus-untuned rates used different iteration caps. Here
both policies decode identical physical errors under two comparisons:

1. **Equal cap:** untuned and selected tuned numerical/prior/damping settings
   both stop at `T=100`.
2. **Approximately equal mean iterations:** untuned BP4 uses a cap selected
   from a separate pilot to match the previously measured mean iterations of
   the selected tuned policy. The tuned policy retains its selected cap.

All arms use the compiled canonical float64 v2 BP4 sum-product kernel with
the same code and physical depolarizing probability `p=0.06`. Untuned means
decoder prior `p0=0.06`, outgoing V2C damping `d=0`, no check cap, product
epsilon `1e-10`. A5's selected settings are `p0=0.005,d=0.2,T=10000`; B2's
are `p0=0.15,d=0.1,T=5000`. The equal-cap arms change only the tuned
policy's iteration cap to 100. The independent evaluator counts Type I
syndrome failures and Type II syndrome-consistent logical failures as block
failures; stabilizer-equivalent corrections count as successes.

The [20,000-shot paired pilot](pilot_plan.json) screened untuned caps 100,
300, 600, 1000, 1600, and 2400 on each code. A5 needed a
[pilot extension](pilot_extension_plan.json) at caps 3000, 3600, and 4200.
The [evaluation plan](evaluation_plan.json) freezes untuned work caps 3000
for A5 and 2400 for B2 before any evaluation shots. It uses fresh seeds and
100,000 paired shots per code. The target work comes from the selected
policies' preceding 100,000-shot stages, avoiding the noisier 20,000-shot
pilot estimate for B2. The pilot is calibration only; its rates do not enter
the final comparison.

The final results, paired rescues/losses, exact 90% intervals, work, and
actual work-matching error are in [REPORT.md](REPORT.md). The plan files
pin registry and implementation hashes. Per-shot ledgers retain sampled
error hashes and independent outcomes. `analyze.py` reconstructs the PCG64
physical sample stream, checks every event digest/count/manifest, and checks
that each arm received the same physical errors.

From the repository root, with the qualified Python environment:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py pilot
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py pilot_extension
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py evaluation
PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/plot.py
```

To reproduce the shots, copy the study to a new identity and run the frozen
task plans with `run_task.py` (pilot/evaluation) or `run_extension.py`
(extension), one task index at a time. The runners refuse to overwrite an
existing evidence directory. Raw event ledgers are retained on the HPC
filesystem and excluded from Git; tracked manifests/summaries contain their
SHA-256 digests.
