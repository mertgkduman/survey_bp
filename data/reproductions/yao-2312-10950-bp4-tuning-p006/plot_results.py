"""Render audited fixed-shot BP4 tuning intervals as standalone figures."""

from __future__ import annotations

import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from runner import ROOT, REPO, load_registry


def plot(stage: str) -> None:
    if stage not in {"refine", "validate", "extend", "followup", "tail_a5", "tail_b2", "sweet_b2", "joint_final", "a5_prior", "b2_prior_confirm", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood"}:
        raise ValueError("unknown stage")
    result = json.loads((ROOT / "results" / f"{stage}_results.json").read_text())
    if not result["complete"]:
        raise ValueError("plot requires a complete audited result")
    plan = json.loads((ROOT / f"{stage}_plan.json").read_text())
    _, candidates, _ = load_registry(REPO / plan["candidate_registry"])
    codes = [code for code in ("a5", "b2")
             if any(row["code"] == code for row in result["rows"])]
    fig, axes = plt.subplots(1, len(codes), figsize=(7.5 * len(codes), 6.8),
                             layout="constrained", squeeze=False)
    for ax, code in zip(axes[0], codes, strict=True):
        rows = sorted((r for r in result["rows"] if r["code"] == code),
                      key=lambda r: (r["failures"], r["mean_iterations"]))
        if stage == "refine":
            rows = rows[:10] + [r for r in rows[10:]
                                if r["candidate_id"] == result["baseline_id"]]
        y = np.arange(len(rows))
        rates = np.array([r["ler"] for r in rows])
        lower = rates - np.array([r["ci90_lower"] for r in rows])
        upper = np.array([r["ci90_upper"] for r in rows]) - rates
        baseline_id = result.get("baseline_by_code", {}).get(code, result["baseline_id"])
        color = ["#777777" if r["candidate_id"] == baseline_id else "#0067a8"
                 for r in rows]
        for j, row in enumerate(rows):
            ax.errorbar(rates[j] * 1000, y[j], xerr=np.array([[lower[j]], [upper[j]]]) * 1000,
                        fmt="o", color=color[j], capsize=2.5, markersize=4)
        labels = []
        for row in rows:
            item = candidates[row["candidate_id"]]
            if item["kernel"] == "profile_v2":
                labels.append(f"float64 d={item['damping']:g}, p₀={item['p0']:g}, T={item['max_iterations']}")
            else:
                policy = item["policy"]
                resolution = policy["resolution"]
                labels.append(f"{policy['check_rule']}, {resolution['format']} "
                              f"s={resolution.get('scale', '—')}, d={policy['damping']:g}, "
                              f"T={item['max_iterations']}")
        ax.set_yticks(y, labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(f"{code.upper()} at physical p = 0.06; N = {rows[0]['shots']:,}")
        ax.set_xlabel("Block logical error rate per 1,000 shots (exact 90% CI)")
        ax.grid(axis="x", alpha=.25)
    title = {"refine": "refinement", "validate": "independent holdout",
             "extend": "A5 cap extension", "followup": "fresh-seed follow-up",
             "tail_a5": "A5 cap tail", "tail_b2": "B2 prior and cap tail",
             "sweet_b2": "B2 local prior check", "joint_final": "final damping and prior check",
             "a5_prior": "A5 local prior check", "b2_prior_confirm": "B2 prior confirmation",
             "a5_low_prior": "A5 lower-prior search", "a5_tiny_prior": "A5 tiny-prior check",
             "a5_final_neighborhood": "A5 damping and cap check",
             "a5_d02_neighborhood": "A5 d=0.2 neighborhood"}[stage]
    fig.suptitle(f"BP4 {title}: paired fixed-shot runs on independent error streams", fontsize=13)
    output = ROOT / "results" / f"{stage}_intervals.png"
    fig.savefig(output, dpi=180)
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("refine", "validate", "extend", "followup", "tail_a5", "tail_b2", "sweet_b2", "joint_final", "a5_prior", "b2_prior_confirm", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood"))
    args = parser.parse_args()
    plot(args.stage)
