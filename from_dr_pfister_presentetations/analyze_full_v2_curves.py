"""Audit and plot the paired full-v2 curve campaign after all 12 point jobs."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results/full_v2_curves"
POINTS = (
    ("b1", "0060", .06), ("b1", "0065", .065),
    ("b1", "0080", .08), ("b1", "0100", .10),
    ("b1", "0120", .12), ("b1", "0140", .14),
    ("double_gross", "0040", .04), ("double_gross", "0050", .05),
    ("double_gross", "0060", .06), ("double_gross", "0080", .08),
    ("double_gross", "0100", .10), ("double_gross", "0120", .12),
)
STYLES = {
    "bp4_vanilla_sp_v2": ("#777777", "o", "BP4 vanilla SP, float64 v2"),
    "bp4_vanilla_ms_q8": ("#9a9a9a", "s", "BP4 vanilla MS, local Q8"),
    "binary_tuned_oms_q8": ("#d55e00", "D", "Binary tuned OMS, local Q8"),
    "binary_tuned_spa_v2": ("#0072b2", "^", "Binary SPA, float64 v2"),
    "bp4_tuned_sp_v2": ("#111111", "o", "BP4 tuned SP, float64 v2"),
}
SOURCE_STYLES = {
    "bp4_vanilla_sp": "#777777", "bp4_vanilla_ms": "#9a9a9a",
    "binary_tuned_oms": "#d55e00", "bp4_tuned_sp": "#111111",
}


def verify_ledger(path: Path, summary: dict) -> int:
    digest = hashlib.sha256()
    n = 0
    with gzip.open(path / summary["event_ledger"], "rb") as handle:
        for line in handle:
            digest.update(line)
            n += 1
    if digest.hexdigest() != summary["uncompressed_event_ledger_sha256"]:
        raise ValueError(f"ledger digest mismatch: {path}")
    expected = sum(arm["shots"] for arm in summary["arms"].values())
    if n != expected:
        raise ValueError(f"ledger record count mismatch: {path}: {n} != {expected}")
    return n


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--skip-ledger-hash", action="store_true")
    args = parser.parse_args()
    source = list(csv.DictReader((ROOT / "results/source_curves.csv").open(newline="", encoding="utf-8")))
    source_by = {(r["code"], r["decoder"], float(r["p"])): r for r in source}
    rows = []
    missing = []
    ledger_count = 0
    for code, label, p in POINTS:
        path = RESULTS / f"{code}_p{label}"
        summary_path = path / "summary.json"
        if not summary_path.exists():
            missing.append(str(path))
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary["code"] != code or abs(summary["physical_p"] - p) > 1e-12:
            raise ValueError(f"point identity mismatch: {path}")
        if not args.skip_ledger_hash:
            ledger_count += verify_ledger(path, summary)
        for arm, value in summary["arms"].items():
            source_row = source_by[("B1_882_24" if code == "b1" else "double_Gross_288_12_18",
                                    value["source_decoder"], p)]
            rows.append({"code": code, "p": p, "arm": arm,
                         "source_decoder": value["source_decoder"],
                         "source_rate_or_bound": source_row["reported_ler"],
                         "source_point_type": source_row["point_type"],
                         "shots": value["shots"], "failures": value["failures"],
                         "type_i": value["type_i"], "type_ii": value["type_ii"],
                         "ler": value["ler"],
                         "lower_95_two_sided": value["lower_95_two_sided"],
                         "upper_95_two_sided": value["upper_95_two_sided"],
                         "upper_95_one_sided_if_zero": value["upper_95_one_sided_if_zero"],
                         "mean_work": value["mean_work"],
                         "mean_elapsed_seconds": value["total_elapsed_seconds"] / value["shots"],
                         "within_local_95_ci": (value["lower_95_two_sided"]
                                                <= float(source_row["reported_ler"])
                                                <= value["upper_95_two_sided"])
                         if source_row["point_type"] == "observed" else "not_applicable"})
    if missing and not args.allow_partial:
        raise SystemExit(f"{len(missing)} incomplete point jobs: {missing}")
    if not rows:
        raise SystemExit("no completed point summaries")
    output = RESULTS / ("partial_comparison.csv" if missing else "comparison.csv")
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), constrained_layout=True)
    for ax, (code, code_id, title) in zip(axes, (("b1", "B1_882_24", "B1 [[882,24]]"),
                                           ("double_gross", "double_Gross_288_12_18", "double-Gross [[288,12,18]]"))):
        for source_name, color in SOURCE_STYLES.items():
            sr = sorted((r for r in source if r["code"] == code_id and r["decoder"] == source_name),
                        key=lambda r: float(r["p"]))
            if sr:
                ax.plot([float(r["p"]) for r in sr], [float(r["reported_ler"]) for r in sr],
                        color=color, linestyle="--", linewidth=1, alpha=.6,
                        label=f"Presentation {source_name}")
        for arm, (color, marker, label) in STYLES.items():
            part = sorted((r for r in rows if r["code"] == code and r["arm"] == arm),
                          key=lambda r: r["p"])
            if not part:
                continue
            x = [r["p"] for r in part]
            y = [float(r["ler"] or r["upper_95_one_sided_if_zero"]) for r in part]
            ax.plot(x, y, color=color, marker=marker, markersize=5, linewidth=1.3,
                    label=label)
            for r, xx, yy in zip(part, x, y):
                if r["failures"] == 0:
                    ax.scatter([xx], [yy], color=color, marker="v", s=42, zorder=5)
                else:
                    low = max(float(r["lower_95_two_sided"]), 1e-9)
                    high = float(r["upper_95_two_sided"])
                    ax.vlines(xx, low, high, colors=color, alpha=.45, linewidth=.7)
        ax.set_title(title)
        ax.set_yscale("log")
        ax.set_ylim(1e-7, 1)
        ax.set_xlabel("Depolarizing probability p")
        ax.grid(True, which="both", alpha=.2)
    axes[0].set_ylabel("Block logical failure rate / zero-failure bound")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(.5, -.08))
    figure = RESULTS / ("partial_curves.png" if missing else "curves.png")
    fig.savefig(figure, dpi=180, bbox_inches="tight")
    plt.close(fig)
    report = {
        "completed_points": len(POINTS) - len(missing), "required_points": len(POINTS),
        "completed_local_arm_points": len(rows), "source_points": len(source),
        "verified_ledger_records": ledger_count if not args.skip_ledger_hash else None,
        "missing": missing, "comparison_csv": output.name, "figure": figure.name,
        "note": "Local-CI inclusion treats the source estimate as a fixed target because most source denominators were not supplied; it is not a two-sample agreement test. Source MS/OMS use separate Q8 controls; binary SPA v2 is a policy adaptation, not the source OMS rule."
    }
    (RESULTS / ("partial_analysis.json" if missing else "analysis.json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Full v2 presentation-curve comparison", "",
             f"Completed {report['completed_points']}/{report['required_points']} code/probability jobs; "
             f"{len(rows)} local arm points for {len(source)} presentation values.", "",
             "Each count is a block failure out of the stated number of paired code-capacity "
             "shots. Type I means no syndrome match; Type II means a matched syndrome "
             "with a nontrivial logical residual. Stabilizer-equivalent outcomes succeed.", "",
             "The source's observed-point denominators were not provided. Its double-Gross "
             "BP4 point at p=.06 is an upper bound, not an observed rate. A source rate "
             "inside a local confidence interval is a descriptive proximity check only.", ""]
    for code, title in (("b1", "B1 [[882,24]]"),
                        ("double_gross", "double-Gross [[288,12,18]]")):
        lines.extend([f"## {title}", "",
                      "| p | Local arm | Failures / N | Local LER or zero bound | "
                      "95% local CI | Source rate/bound | Type I / II | Mean BP4 work |",
                      "|---:|---|---:|---:|---:|---:|---:|---:|"])
        for r in sorted((r for r in rows if r["code"] == code),
                        key=lambda x: (x["p"], x["arm"])):
            local = (float(r["ler"]) if r["failures"] else
                     float(r["upper_95_one_sided_if_zero"]))
            suffix = " (upper)" if r["failures"] == 0 else ""
            source_suffix = " (upper)" if r["source_point_type"] != "observed" else ""
            lines.append(
                f"| {r['p']:.3f} | `{r['arm']}` | {r['failures']:,}/{r['shots']:,} | "
                f"{local:.3g}{suffix} | "
                f"[{float(r['lower_95_two_sided']):.3g}, {float(r['upper_95_two_sided']):.3g}] | "
                f"{float(r['source_rate_or_bound']):.3g}{source_suffix} | "
                f"{r['type_i']:,} / {r['type_ii']:,} | {float(r['mean_work']):.3g} |"
            )
        lines.append("")
    lines.extend(["## Interpretation limits", "",
                  "The float64 v2 BP4 arms change the presentation's Q8 numerical policy; "
                  "the binary SPA v2 arm also changes the presentation's OMS check rule. "
                  "The local Q8 MS/OMS controls are experimental implementations, not "
                  "the canonical v2 kernels. Differences therefore identify a curve gap "
                  "but do not by themselves identify its mechanism.", "",
                  "The planned sample counts were fixed before these runs from the "
                  "source rates. When a local rate is much higher or lower, its observed "
                  "failure count can differ substantially from the target of 30.", "",
                  f"Ledger verification: {ledger_count:,} records checked." if not args.skip_ledger_hash
                  else "Ledger hash verification was skipped in this analysis run.", ""])
    markdown = RESULTS / ("partial_report.md" if missing else "REPORT.md")
    markdown.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
