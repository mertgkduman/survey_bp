"""Render the audited equal-cap and work-controlled BP4 rate intervals."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FAIR = Path(__file__).resolve().parent


def main() -> None:
    result = json.loads((FAIR / "evaluation_results.json").read_text())
    plan = json.loads((FAIR / "evaluation_plan.json").read_text())
    if not result["complete"]:
        raise ValueError("complete audited evaluation required")
    rows = {(r["code"], r["candidate_id"]): r for r in result["rows"]}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for ax, code in zip(axes, ("a5", "b2"), strict=True):
        cap = plan["work_caps"][code]
        arms = [("vanilla_t100", "Untuned, T=100"),
                (f"tuned_t100_{code}", "Tuned parameters, T=100"),
                (f"vanilla_work_{code}", f"Untuned, T={cap:,}"),
                (f"tuned_selected_{code}", "Tuned, selected cap")]
        for i, (name, label) in enumerate(arms):
            row = rows[(code, name)]
            rate = row["ler"]
            lo = row["ci90_lower"]
            hi = row["ci90_upper"]
            ax.errorbar(rate, i, xerr=np.array([[rate - lo], [hi - rate]]),
                        fmt="o", color="#0067a8" if "tuned" in name else "#8b6b3e",
                        capsize=3, markersize=6)
            ax.text(hi * 1.09, i, f"{row['mean_iterations']:.2f} iters", va="center", fontsize=8)
        ax.set_yticks(range(4), [label for _, label in arms])
        ax.set_xscale("log")
        ax.set_xlim(1e-4, 1e-2)
        ax.set_ylim(3.6, -.6)
        ax.set_title(f"{code.upper()} · physical p=0.06 · N=100,000")
        ax.grid(axis="x", alpha=.25)
        ax.set_xlabel("Block failure rate (exact 90% CI)")
    fig.suptitle("BP4: equal cap and approximately equal mean work", fontsize=13)
    fig.savefig(FAIR / "comparison.png", dpi=180)
    fig.savefig(FAIR / "comparison.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
