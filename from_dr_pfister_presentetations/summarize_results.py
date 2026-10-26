"""Create an exact-binomial pilot table without merging source and local data."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent


def main() -> None:
    with (ROOT / "results/source_curves.csv").open(newline="", encoding="utf-8") as handle:
        source = {(row["code"], row["decoder"], float(row["p"])): row for row in csv.DictReader(handle)}
    rows = []
    for path in sorted((ROOT / "results").glob("pilot_*.json")):
        result = json.loads(path.read_text())
        if result["max_iterations"] != 1000:
            continue
        for arm, item in result["arms"].items():
            n, k = result["shots"], item["failures"]
            ci = binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
            reported = source.get((result["code"], arm, result["p"]))
            rows.append({
                "code": result["code"], "p": result["p"], "decoder": arm,
                "local_failures": k, "local_trials": n, "local_ler": item["ler"],
                "local_95_exact_two_sided_low": ci.low, "local_95_exact_two_sided_high": ci.high,
                "reported_ler_or_upper": "" if reported is None else reported["reported_ler"],
                "reported_point_type": "" if reported is None else reported["point_type"],
                "mean_bp4_equivalent_work": item["mean_bp4_equivalent_work"],
                "p99_bp4_equivalent_work": item["p99_bp4_equivalent_work"],
                "invalid_syndrome": item["invalid_syndrome"], "pilot_file": path.name,
            })
    output = ROOT / "results/pilot_summary.csv"
    if rows:
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    pairs = []
    for path in sorted((ROOT / "results").glob("pilot_*.json")):
        result = json.loads(path.read_text())
        if result["max_iterations"] != 1000:
            continue
        for comparison, counts in result["paired"].items():
            rescue, loss = counts["rescue"], counts["loss"]
            total = rescue + loss
            pvalue = binomtest(rescue, total, 0.5).pvalue if total else 1.0
            pairs.append({"code": result["code"], "p": result["p"], "comparison": comparison,
                          "trials": result["shots"], "rescues": rescue, "losses": loss,
                          "net_failure_reduction": rescue - loss, "exact_paired_binomial_two_sided_p": pvalue,
                          "pilot_file": path.name})
    if pairs:
        with (ROOT / "results/pilot_paired_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pairs[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(pairs)
    print(output)


if __name__ == "__main__":
    main()
