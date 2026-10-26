"""Audit matched BP4 reference-gap ablations and write a compact results table."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent / "results/performance_investigation"
RUNS = {
    "b1": ("tie_q8_b1_n200", "tie_float_b1_n200", "reference_check_clipped_b1_n200",
           "boxplus_unclipped_b1_n200", "reference_float_b1_n200"),
    "double_gross": ("tie_q8_gross_n1000", "tie_float_gross_n1000",
                     "reference_check_clipped_gross_n1000", "projection_clipped_gross_n1000",
                     "posterior_v2c_clipped_gross_n1000", "boxplus_unclipped_gross_n1000",
                     "reference_float_gross_n1000"),
}


def audited_run(name: str) -> tuple[dict, list[dict]]:
    folder = ROOT / name
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    data = (folder / "events.jsonl").read_bytes()
    assert hashlib.sha256(data).hexdigest() == summary["event_ledger_sha256"], name
    records = [json.loads(line) for line in data.splitlines()]
    assert len(records) == summary["shots"], name
    assert [record["shot"] for record in records] == list(range(summary["shots"])), name
    return summary, records


def row(code: str, name: str, arm: str, summary: dict, records: list[dict]) -> dict:
    outcomes = [record[arm] for record in records]
    failures = sum(item["failed"] for item in outcomes)
    type_i = sum(not item["valid_syndrome"] for item in outcomes)
    type_ii = sum(item["logical_failure"] for item in outcomes)
    exact = sum(item["exact_correction"] for item in outcomes)
    degenerate = sum(item["valid_syndrome"] and not item["logical_failure"] and not item["exact_correction"]
                     for item in outcomes)
    assert failures == type_i + type_ii
    assert failures + exact + degenerate == len(outcomes)
    interval = binomtest(failures, len(outcomes)).proportion_ci(method="exact")
    return {"code": code, "run": name, "arm": arm, "shots": len(outcomes),
            "failures": failures, "type_i_invalid_syndrome": type_i,
            "type_ii_valid_syndrome_logical": type_ii, "exact_success": exact,
            "stabilizer_equivalent_success": degenerate,
            "ler": failures / len(outcomes), "ci95_low": interval.low,
            "ci95_high": interval.high,
            "zero_failure_one_sided_95_upper": 1 - .05 ** (1 / len(outcomes)) if failures == 0 else "",
            "mean_iterations": sum(item.get("iterations", item.get("first_valid_iteration", -1)
                                                  if item.get("first_valid_iteration", -1) >= 0 else 1000)
                                   for item in outcomes) / len(outcomes)}


def main() -> None:
    rates = []
    pairs = []
    for code, names in RUNS.items():
        audited = {name: audited_run(name) for name in names}
        hashes = [[record["error_sha256"] for record in audited[name][1]] for name in names]
        assert all(hash_list == hashes[0] for hash_list in hashes), code
        for name in names:
            summary, records = audited[name]
            arms = ("ordinary", "reference_tie") if summary["kernel"] in ("float", "q8") else (
                "reference_float" if summary["kernel"] == "reference_float" else "variant",)
            for arm in arms:
                result = row(code, name, arm, summary, records)
                prefix = arm if summary["kernel"] in ("float", "q8") else (
                    "reference_float" if summary["kernel"] == "reference_float" else "variant")
                assert result["failures"] == summary["counts"][f"{prefix}_failed"], name
                assert result["type_i_invalid_syndrome"] == summary["counts"][f"{prefix}_invalid"], name
                rates.append(result)
        old_name, old_arm = (("b1_transfer_p010_n200_seed20261101", "q8_s4_d01_p10") if code == "b1"
                             else ("gross_holdout_p008_n1000_seed20261031", "q8_s4_d01_p08"))
        old_events = [json.loads(line) for line in (ROOT / old_name / "events.jsonl").read_text().splitlines()
                      if json.loads(line)["arm"] == old_arm]
        new_events = audited[names[0]][1]
        assert len(old_events) == len(new_events)
        for old, new in zip(old_events, new_events):
            assert old["error_sha256"] == new["error_sha256"]
            assert old["failed"] == new["ordinary"]["failed"]
            assert old["iterations"] == (new["ordinary"]["first_valid_iteration"]
                                         if new["ordinary"]["first_valid_iteration"] >= 0 else 1000)
        references = ((names[0], "ordinary", names[0], "reference_tie"),
                      (names[1], "ordinary", names[1], "reference_tie"),
                      *((names[1], "ordinary", name, "reference_float" if name.startswith("reference_float") else "variant")
                        for name in names[2:]))
        for old_name, old_arm, new_name, new_arm in references:
            old = audited[old_name][1]
            new = audited[new_name][1]
            pairs.append({"code": code, "reference_run": old_name, "reference_arm": old_arm,
                          "new_run": new_name, "new_arm": new_arm,
                          "rescues": sum(a[old_arm]["failed"] and not b[new_arm]["failed"] for a, b in zip(old, new)),
                          "losses": sum(not a[old_arm]["failed"] and b[new_arm]["failed"] for a, b in zip(old, new))})
    for file, items in (("reference_gap_rates.csv", rates), ("reference_gap_paired.csv", pairs)):
        with (ROOT / file).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=items[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(items)
    plot(rates)
    print(f"Audited {len(rates)} arms and {len(pairs)} paired contrasts on identical error hashes.")


def plot(rates: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "bp4-reference-gap-v1"
    import matplotlib.pyplot as plt

    selected = {
        "b1": (("tie_q8_b1_n200", "ordinary"), ("tie_float_b1_n200", "ordinary"),
               ("tie_float_b1_n200", "reference_tie"), ("reference_float_b1_n200", "reference_float")),
        "double_gross": (("tie_q8_gross_n1000", "ordinary"), ("tie_float_gross_n1000", "ordinary"),
                         ("tie_float_gross_n1000", "reference_tie"),
                         ("reference_float_gross_n1000", "reference_float")),
    }
    lookup = {(item["run"], item["arm"]): item for item in rates}
    labels = ("Q8 tuned SP", "F64 clipped\nlocal tie", "F64 clipped\nreference tie",
              "F64 reference\nnumerics")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, code in zip(axes, selected, strict=True):
        for index, key in enumerate(selected[code]):
            value = lookup[key]
            if value["failures"] == 0:
                y = value["zero_failure_one_sided_95_upper"]
                ax.plot(index, y, marker="v", markersize=8, markerfacecolor="white",
                        markeredgecolor="#164b7a", linestyle="none")
            else:
                y = value["ler"]
                ax.errorbar(index, y,
                            yerr=[[y - value["ci95_low"]], [value["ci95_high"] - y]],
                            fmt="o", markersize=7, capsize=3, color="#164b7a")
            ax.annotate(f'{value["failures"]}/{value["shots"]}', (index, y),
                        xytext=(0, 7), textcoords="offset points", ha="center", fontsize=9)
        ax.set(title="B1, p=0.10" if code == "b1" else "double-Gross, p=0.08",
               yscale="log", ylim=(3e-4, 2), ylabel="Block logical error rate",
               xlim=(-.5, 3.5), xticks=range(4), xticklabels=labels)
        ax.grid(axis="y", alpha=.25)
    fig.suptitle("BP4 policies on matched errors; exact 95% binomial intervals", fontsize=12)
    fig.text(.5, .01, "Downward triangles: one-sided 95% upper bound when zero failures were observed",
             ha="center", fontsize=9)
    fig.subplots_adjust(left=.085, right=.985, bottom=.24, top=.80, wspace=.25)
    for extension in ("png", "svg"):
        fig.savefig(ROOT / f"reference_gap_comparison.{extension}", dpi=170,
                    bbox_inches="tight", metadata={"Date": None} if extension == "svg" else None)
    plt.close(fig)
    svg = ROOT / "reference_gap_comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
                   + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
