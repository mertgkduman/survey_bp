"""Compare reported presentation points with local rates under p-axis shifts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent
ARMS = ("bp4_vanilla_sp", "bp4_tuned_sp", "binary_tuned_oms")
TARGETS = (("B1_882_24", 0.10), ("double_Gross_288_12_18", 0.08),
           ("double_Gross_288_12_18", 0.12))


def lookup_pilot(pilots: list[dict], code: str, p: float) -> dict:
    matches = [item for item in pilots if item["code"] == code and item["max_iterations"] == 1000
               and math.isclose(item["p"], p, rel_tol=0, abs_tol=1e-12)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one local pilot for {code}, p={p}: {len(matches)}")
    return matches[0]


def main() -> None:
    with (ROOT / "results/source_curves.csv").open(newline="", encoding="utf-8") as handle:
        source = {(row["code"], row["decoder"], float(row["p"])): row for row in csv.DictReader(handle)}
    pilots = [json.loads(path.read_text()) for path in (ROOT / "results").glob("pilot_*.json")]
    rows: list[dict] = []
    for hypothesis, factor, targets in (
        ("unshifted", 1.0, TARGETS),
        ("presentation_x_multiplied_by_2_over_3", 2.0 / 3.0, TARGETS),
        ("presentation_x_multiplied_by_3_over_2", 1.5, (("double_Gross_288_12_18", 0.08),)),
    ):
        for code, slide_p in targets:
            local = lookup_pilot(pilots, code, factor * slide_p)
            for arm in ARMS:
                source_row = source[(code, arm, slide_p)]
                if source_row["point_type"] != "observed":
                    raise ValueError("shift analysis requires observed source rates")
                n, failures = local["shots"], local["arms"][arm]["failures"]
                reported = float(source_row["reported_ler"])
                interval = binomtest(failures, n).proportion_ci(confidence_level=0.95, method="exact")
                rows.append({
                    "hypothesis": hypothesis, "code": code, "decoder": arm,
                    "slide_label_p": slide_p, "local_physical_p": local["p"],
                    "slide_reported_ler": reported, "local_failures": failures, "local_trials": n,
                    "local_ler": failures / n, "local_exact_95_low": interval.low,
                    "local_exact_95_high": interval.high,
                    "local_one_sided_95_upper_if_zero": 1 - 0.05 ** (1 / n) if failures == 0 else "",
                    "binomial_p_if_slide_rate_exact": binomtest(failures, n, reported).pvalue,
                    "local_pilot_ledger": local["event_ledger"],
                    "local_pilot_ledger_sha256": local["event_ledger_sha256"],
                })
    output = ROOT / "results/p_axis_shift_comparison.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), constrained_layout=True, sharey=True)
    for axis, (code, slide_p) in zip(axes, TARGETS, strict=True):
        subset = [row for row in rows if row["code"] == code and row["slide_label_p"] == slide_p
                  and row["hypothesis"] in {"unshifted", "presentation_x_multiplied_by_2_over_3"}]
        positions = np.arange(len(ARMS))
        width = 0.26
        for arm_index, arm in enumerate(ARMS):
            arm_rows = {row["hypothesis"]: row for row in subset if row["decoder"] == arm}
            slide = arm_rows["unshifted"]["slide_reported_ler"]
            axis.bar(positions[arm_index] - width, slide, width, color="#999999", hatch="//",
                     edgecolor="black", linewidth=0.3, label="slide" if arm_index == 0 else None)
            for hypothesis, offset, color, label in (
                ("unshifted", 0.0, "#0072b2", "local at labeled p"),
                ("presentation_x_multiplied_by_2_over_3", width, "#d55e00", "local at 2p/3"),
            ):
                item = arm_rows[hypothesis]
                value = (item["local_ler"] if item["local_failures"]
                         else item["local_one_sided_95_upper_if_zero"])
                axis.bar(positions[arm_index] + offset, value, width, color=color,
                         edgecolor="black", linewidth=0.3, label=label if arm_index == 0 else None)
                if item["local_failures"] == 0:
                    axis.plot(positions[arm_index] + offset, value, marker="v", markerfacecolor="white",
                              markeredgecolor="black", markersize=7)
        axis.set_xticks(positions, ["vanilla\nBP4 SP", "tuned\nBP4 SP", "tuned\nbinary OMS"])
        axis.set_title(f"{'B1' if code.startswith('B1') else 'double-Gross'}: slide p={slide_p:.2f}")
        axis.set_yscale("log")
        axis.set_ylim(1e-4, 1)
        axis.grid(axis="y", which="major", alpha=0.2)
        if axis is axes[0]:
            axis.set_ylabel("Failure rate (triangle = zero-failure 95% upper bound)")
            axis.legend(fontsize=7)
    fig.savefig(ROOT / "plots/p_axis_shift_comparison.png", dpi=180)
    svg_path = ROOT / "plots/p_axis_shift_comparison.svg"
    fig.savefig(svg_path)
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
