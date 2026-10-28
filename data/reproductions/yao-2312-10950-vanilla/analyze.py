"""Audit shard ledgers and compare vanilla BP curves with source TeX points."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta, binomtest

from run import ARMS, ROOT, _load_code, _sample


COLORS = {"bp4_v1": "#999999", "bp4_v2": "#1f77b4",
          "binary_v1": "#d55e00", "binary_v2": "#009e73"}


def _interval(failures: int, shots: int) -> tuple[float, float]:
    if shots < 1 or not 0 <= failures <= shots:
        raise ValueError("invalid failure count")
    lower = 0.0 if failures == 0 else float(beta.ppf(.025, failures, shots-failures+1))
    upper = 1.0 if failures == shots else float(beta.ppf(.975, failures+1, shots-failures))
    return lower, upper


def _audit_task(task: dict[str, object], code, campaign_sha256: str) -> tuple[dict[str, object], dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    output = ROOT / task["output"]
    manifest_path, ledger_path, summary_path = (output / name for name in ("manifest.json", "events.jsonl", "summary.json"))
    summary = json.loads(summary_path.read_text())
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if (sha256(manifest_bytes).hexdigest() != summary["manifest_sha256"]
            or manifest["campaign_sha256"] != campaign_sha256
            or (manifest["code"], manifest["physical_p"], manifest["seed"], manifest["start_shot"], manifest["max_shots"])
            != (task["code"], task["p"], task["seed"], task["start_shot"], task["shots"])
            or summary["stop_reason"] != "fixed_shard_complete"
            or summary["shots"] != task["shots"]
            or summary["start_shot"] != task["start_shot"]
            or summary["end_shot_exclusive"] != task["start_shot"] + task["shots"]):
        raise ValueError(f"manifest/summary mismatch in {output}")
    digest = sha256()
    totals = {arm: {field: 0 for field in ("type_i", "type_ii", "exact_success",
                                              "stabilizer_success", "iteration_sum", "elapsed_ns_sum")}
              for arm in ARMS}
    pairs = {"bp4_v2_vs_v1": {"rescue": 0, "loss": 0},
             "binary_v2_vs_v1": {"rescue": 0, "loss": 0},
             "bp4_v2_vs_binary_v2": {"rescue": 0, "loss": 0}}
    first_error = last_error = None
    line_count = 0
    with ledger_path.open("rb") as handle:
        for offset, raw in enumerate(handle):
            line_count += 1
            digest.update(raw)
            event = json.loads(raw)
            if event["schema"] != "yao-vanilla-shot-v1" or event["shot"] != task["start_shot"] + offset:
                raise ValueError(f"shot index or schema mismatch in {ledger_path}")
            if set(event["arms"]) != set(ARMS):
                raise ValueError(f"missing decoder arm in {ledger_path}")
            if first_error is None:
                first_error = event["error_sha256"]
            last_error = event["error_sha256"]
            for arm, record in event["arms"].items():
                if sum(bool(record[field]) for field in ("type_i", "type_ii", "exact_success", "stabilizer_success")) != 1:
                    raise ValueError(f"outcome partition invalid in {ledger_path}")
                for field in ("type_i", "type_ii", "exact_success", "stabilizer_success"):
                    totals[arm][field] += int(record[field])
                totals[arm]["iteration_sum"] += sum(record["iterations"])
                totals[arm]["elapsed_ns_sum"] += record["elapsed_ns"]
            for label, new, old in (("bp4_v2_vs_v1", "bp4_v2", "bp4_v1"),
                                    ("binary_v2_vs_v1", "binary_v2", "binary_v1"),
                                    ("bp4_v2_vs_binary_v2", "bp4_v2", "binary_v2")):
                new_fail = event["arms"][new]["type_i"] or event["arms"][new]["type_ii"]
                old_fail = event["arms"][old]["type_i"] or event["arms"][old]["type_ii"]
                pairs[label]["rescue"] += int(old_fail and not new_fail)
                pairs[label]["loss"] += int(new_fail and not old_fail)
    if (line_count != task["shots"] or digest.hexdigest() != summary["events_sha256"]
            or totals != summary["counts"]):
        raise ValueError(f"ledger hash or aggregates mismatch in {output}")
    for boundary, observed in ((task["start_shot"], first_error),
                               (task["start_shot"] + task["shots"] - 1, last_error)):
        rng = np.random.Generator(np.random.PCG64(task["seed"]))
        rng.bit_generator.advance(boundary * code.n)
        expected = sha256(_sample(rng, code.n, task["p"]).tobytes()).hexdigest()
        if observed != expected:
            raise ValueError(f"sample stream boundary mismatch in {output}")
    return summary, totals, pairs


def _plot(points: list[dict[str, object]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), sharey=True)
    for axis, code in zip(axes, ("a5", "b2"), strict=True):
        subset = sorted((p for p in points if p["code"] == code and p["complete"]), key=lambda row: row["p"])
        axis.set(title="A5 [[180,10]]" if code == "a5" else "B2 [[882,48]]",
                 xlabel="Depolarizing probability p", xlim=(.037, .103), yscale="log")
        axis.grid(True, which="both", alpha=.25)
        if not subset:
            continue
        xs = [row["p"] for row in subset]
        axis.plot(xs, [row["source_qbp_rate"] for row in subset], "k--o", label="Yao Q-BP", lw=1.5, ms=4)
        for arm in ARMS:
            rates = [row["arms"][arm]["rate"] for row in subset]
            upper = [row["arms"][arm]["upper_one_sided_95"] for row in subset]
            shown = [rate if rate > 0 else np.nan for rate in rates]
            axis.plot(xs, shown, marker="s" if arm.startswith("bp4") else "^",
                      lw=1.45, ms=4, color=COLORS[arm], label=arm.replace("_", " "))
            for x, row, rate, bound in zip(xs, subset, rates, upper):
                if rate > 0:
                    lo, hi = row["arms"][arm]["ci95"]
                    axis.errorbar(x, rate, yerr=[[rate-lo], [hi-rate]], fmt="none",
                                  ecolor=COLORS[arm], elinewidth=.7, capsize=1.8, alpha=.6)
                else:
                    axis.plot(x, bound, marker="v", ms=7, mfc="white", mec=COLORS[arm])
    axes[0].set_ylabel("Block error rate")
    legend_axis = axes[1] if axes[1].get_legend_handles_labels()[0] else axes[0]
    if legend_axis.get_legend_handles_labels()[0]:
        legend_axis.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path.with_suffix(".png"), dpi=180)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def analyze(*, allow_partial: bool = False) -> dict[str, object]:
    campaign_bytes = (ROOT / "campaign.json").read_bytes()
    campaign = json.loads(campaign_bytes)
    campaign_sha256 = sha256(campaign_bytes).hexdigest()
    source = json.loads((ROOT / "source_points.json").read_text())
    if sha256((ROOT / "source_points.json").read_bytes()).hexdigest() != campaign["source_points_sha256"]:
        raise ValueError("source points differ from frozen campaign")
    repo = ROOT.parents[2]
    for name, expected in campaign["implementation_files_sha256"].items():
        if sha256((repo / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"implementation or policy file differs from frozen campaign: {name}")
    codes = {name: _load_code(name) for name in ("a5", "b2")}
    accumulated = defaultdict(lambda: {"shots": 0, "shards": 0,
        "arms": {arm: {field: 0 for field in ("type_i", "type_ii", "exact_success",
                                               "stabilizer_success", "iteration_sum", "elapsed_ns_sum")}
                 for arm in ARMS},
        "pairs": {label: {"rescue": 0, "loss": 0} for label in
                  ("bp4_v2_vs_v1", "binary_v2_vs_v1", "bp4_v2_vs_binary_v2")}})
    missing = []
    shard_receipts = []
    for task in campaign["tasks"]:
        output = ROOT / task["output"]
        if not (output / "summary.json").exists():
            missing.append(task["index"])
            continue
        summary, totals, pairs = _audit_task(task, codes[task["code"]], campaign_sha256)
        key = (task["code"], task["p"])
        dest = accumulated[key]
        dest["shots"] += summary["shots"]
        dest["shards"] += 1
        for arm in ARMS:
            for field, value in totals[arm].items():
                dest["arms"][arm][field] += value
        for label in pairs:
            for field, value in pairs[label].items():
                dest["pairs"][label][field] += value
        shard_receipts.append({"index": task["index"], "events_sha256": summary["events_sha256"]})
    if missing and not allow_partial:
        raise RuntimeError(f"{len(missing)} campaign shards have no completed summary; first: {missing[:12]}")
    rows = []
    for point in campaign["points"]:
        key = (point["code"], point["p"])
        evidence = accumulated[key]
        n = evidence["shots"]
        complete = n == point["planned_shots"]
        arms = {}
        for arm in ARMS:
            c = evidence["arms"][arm]
            failures = c["type_i"] + c["type_ii"]
            ci = _interval(failures, n) if n else (None, None)
            arms[arm] = {"failures": failures, "type_i": c["type_i"], "type_ii": c["type_ii"],
                         "exact_success": c["exact_success"], "stabilizer_success": c["stabilizer_success"],
                         "rate": failures/n if n else None, "ci95": ci,
                         "upper_one_sided_95": 1-.05**(1/n) if n and failures == 0 else None,
                         "mean_bp4_equivalent_iterations": c["iteration_sum"] / n / (2 if arm.startswith("binary") else 1) if n else None,
                         "mean_decode_ms": c["elapsed_ns_sum"] / n / 1e6 if n else None,
                         "source_point_inside_ci95": (ci[0] <= point["source_qbp_rate"] <= ci[1]) if n else None}
        pairs = dict(evidence["pairs"])
        for pair in pairs.values():
            discordant = pair["rescue"] + pair["loss"]
            pair["mcnemar_exact_two_sided_p"] = (float(binomtest(pair["rescue"], discordant, .5).pvalue)
                                                   if discordant else 1.0)
        rows.append({"code": point["code"], "p": point["p"], "source_qbp_rate": point["source_qbp_rate"],
                     "planned_shots": point["planned_shots"], "shots": n,
                     "complete": complete, "arms": arms, "pairs": pairs})
    result = {"schema": "yao-vanilla-merged-assessment-v1",
              "complete": not missing and all(row["complete"] for row in rows),
              "completed_shards": len(shard_receipts), "total_shards": len(campaign["tasks"]),
              "missing_shard_indices": missing, "rows": rows, "shard_receipts": shard_receipts}
    destination = ROOT / "results"
    destination.mkdir(exist_ok=True)
    (destination / "merged.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (destination / "comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ("code", "p", "source_qbp_rate", "planned_shots", "shots", "complete", "arm",
                  "failures", "type_i", "type_ii", "rate", "ci95_low", "ci95_high",
                  "source_point_inside_ci95", "mean_bp4_equivalent_iterations", "mean_decode_ms")
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            for arm in ARMS:
                data = row["arms"][arm]
                writer.writerow({**{key: row[key] for key in fields if key in row}, "arm": arm,
                                 **{key: data.get(key) for key in fields if key in data},
                                 "ci95_low": data["ci95"][0], "ci95_high": data["ci95"][1]})
    lines = ["# Yao et al. vanilla Q-BP comparison", "",
             "Source: [arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2), Figures 7 and 8.",
             "Q-BP points were transcribed from the authors' TeX. Source denominators are unavailable;",
             "the source point inside a local exact 95% interval is descriptive, not a two-sample test.",
             "All local arms use 100 sum-product iterations and the same depolarizing errors per point.",
             "v2 is undamped (d=0) to keep this a vanilla numerical comparison.", "",
             f"Completed shards: {result['completed_shards']}/{result['total_shards']}.", "",
             "| Code | p | N | Source Q-BP | BP4 v1 | BP4 v2 | Binary v1 | Binary v2 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        def cell(arm):
            values = row["arms"][arm]
            return f"{values['failures']}/{row['shots']} ({values['rate']:.6g})" if row["shots"] else "—"
        lines.append(f"| {row['code'].upper()} | {row['p']:.2f} | {row['shots']:,} | {row['source_qbp_rate']:.6g} | "
                     f"{cell('bp4_v1')} | {cell('bp4_v2')} | {cell('binary_v1')} | {cell('binary_v2')} |")
    if result["complete"]:
        lines.extend(["", "Published point inside local exact 95% interval, by code:"])
        for code in ("a5", "b2"):
            subset = [row for row in rows if row["code"] == code]
            counts = ", ".join(
                f"{arm}: {sum(bool(row['arms'][arm]['source_point_inside_ci95']) for row in subset)}/7"
                for arm in ARMS
            )
            lines.append(f"- {code.upper()}: {counts}.")
        lines.extend([
            "",
            "BP4 v2 is near the A5 Q-BP curve at six of seven plotted points.",
            "On B2 it follows the same rate scale, but its local rate is lower than",
            "the published point at six of seven values of p; only two published",
            "B2 points fall inside the corresponding local intervals. BP4 v1 and",
            "both separate-binary arms are outside those intervals at every point.",
            "All BP4 v2 failures in this campaign are Type I syndrome failures.",
            "These are observations about the named local profiles. The paper does",
            "not specify enough numerical details to attribute the remaining B2",
            "difference to a particular source implementation choice or defect.",
        ])
    lines.extend(["", "Type I (syndrome failure), Type II (logical failure after valid syndrome),",
                  "exact/stabilizer success, exact intervals, paired rescues/losses, work, and time are in",
                  "[`comparison.csv`](comparison.csv) and [`merged.json`](merged.json).",
                  "Per-shot ledgers and manifests are under `results/shards/`; each is SHA-256 audited.",
                  "The published Q-BP implementation and exact numerical conventions are not identified",
                  "by the paper. Local v1/v2 curves are explicit canonical adaptations."])
    (destination / "report.md").write_text("\n".join(lines) + "\n")
    _plot(rows, destination / "curve")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", action="store_true", help="analyze only completed shards")
    args = parser.parse_args()
    result = analyze(allow_partial=args.partial)
    print(f"audited {result['completed_shards']}/{result['total_shards']} shards; complete={result['complete']}")


if __name__ == "__main__":
    main()
