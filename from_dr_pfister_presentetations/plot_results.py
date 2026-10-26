"""Plot transcribed slide curves and optional fresh paired-pilot measurements."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
STYLES = {
    "bp4_vanilla_sp": ("#888888", "o", "--", "vanilla BP4, SP"),
    "bp4_vanilla_ms": ("#bbbbbb", "s", ":", "vanilla BP4, MS"),
    "binary_tuned_oms": ("#d55e00", "D", "-", "tuned binary BP"),
    "bp4_tuned_sp": ("#000000", "o", "-", "tuned BP4"),
}
CODES = {"B1_882_24": "B1 [[882,24]]", "double_Gross_288_12_18": "double-Gross [[288,12,18]]"}


def main() -> None:
    with (ROOT / "results/source_curves.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), constrained_layout=True)
    for axis, (code, title) in zip(axes, CODES.items(), strict=True):
        for decoder, (color, marker, linestyle, label) in STYLES.items():
            points = sorted((row for row in rows if row["code"] == code and row["decoder"] == decoder), key=lambda row: float(row["p"]))
            axis.plot([float(row["p"]) for row in points], [float(row["reported_ler"]) for row in points],
                      color=color, marker=marker, linestyle=linestyle, linewidth=1.7, markersize=4.5, label=label)
            for row in points:
                if row["point_type"] == "upper_95_one_sided":
                    axis.plot(float(row["p"]), float(row["reported_ler"]), marker="v", markersize=8,
                              markerfacecolor="white", markeredgecolor=color, linestyle="None", zorder=5)
        axis.set(title=title, xlabel="Depolarizing probability p", ylabel="Logical error rate", yscale="log", ylim=(5e-6, 1))
        axis.grid(True, which="major", alpha=0.25)
        axis.grid(True, which="minor", alpha=0.1)
        axis.legend(fontsize=8)
    output = ROOT / "plots/source_curves.png"
    fig.savefig(output, dpi=180)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)

    pilots = [json.loads(path.read_text()) for path in sorted((ROOT / "results").glob("pilot_*.json"))]
    pilots = [result for result in pilots if result["max_iterations"] == 1000]
    if not pilots:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), constrained_layout=True)
    for axis, (code, title) in zip(axes, CODES.items(), strict=True):
        for decoder, (color, marker, _, label) in STYLES.items():
            points = []
            for result in pilots:
                if result["code"] == code and decoder in result["arms"]:
                    points.append((result["p"], result["shots"], result["arms"][decoder]))
            points.sort(key=lambda item: item[0])
            if points:
                for index, (p, n, arm) in enumerate(points):
                    value = arm["ler"] if arm["failures"] else 1.0 - 0.05 ** (1.0 / n)
                    axis.plot(p, value, color=color, marker="v" if arm["failures"] == 0 else marker,
                              markerfacecolor="white" if arm["failures"] == 0 else color,
                              linestyle="None", label=label if index == 0 else None)
        axis.set(title=f"Local paired pilot: {title}", xlabel="Depolarizing probability p", ylabel="LER or 95% upper bound",
                 yscale="log", ylim=(1e-3, 1))
        axis.grid(True, which="major", alpha=0.25)
        if code == "B1_882_24":
            axis.legend(fontsize=8, loc="upper right")
    output = ROOT / "plots/pilot_curves.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)

    source_lookup = {(row["code"], row["decoder"], float(row["p"])): float(row["reported_ler"]) for row in rows}
    selected = sorted((item for item in pilots
                       if (item["code"], "bp4_vanilla_sp", item["p"]) in source_lookup
                       and (item["code"], "bp4_tuned_sp", item["p"]) in source_lookup),
                      key=lambda item: (item["code"], item["p"]))
    if selected:
        fig, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
        positions = np.arange(len(selected))
        width = 0.19
        series = (
            ("bp4_vanilla_sp", "slide vanilla BP4", "#b0b0b0", -1.5, True),
            ("bp4_vanilla_sp", "local vanilla BP4", "#666666", -0.5, False),
            ("bp4_tuned_sp", "slide tuned BP4", "#777777", 0.5, True),
            ("bp4_tuned_sp", "local tuned BP4", "#111111", 1.5, False),
        )
        for decoder, label, color, offset, is_slide in series:
            values = [source_lookup[(item["code"], decoder, item["p"])] if is_slide
                      else item["arms"][decoder]["ler"] for item in selected]
            axis.bar(positions + offset * width, values, width, color=color, label=label,
                     hatch="//" if is_slide else None, edgecolor="black", linewidth=0.4)
        axis.set_xticks(positions, [f"{'B1' if item['code'].startswith('B1') else 'double-Gross'}\np={item['p']:.2f}, N={item['shots']}"
                                    for item in selected])
        axis.set(yscale="log", ylim=(1e-4, 1), ylabel="Logical error rate", title="Presentation rates and local Q8 policy pilots")
        axis.grid(axis="y", which="major", alpha=0.2)
        axis.legend(ncol=2, fontsize=8)
        fig.savefig(ROOT / "plots/pilot_vs_source.png", dpi=180)
        fig.savefig(ROOT / "plots/pilot_vs_source.svg")
        plt.close(fig)


if __name__ == "__main__":
    main()
