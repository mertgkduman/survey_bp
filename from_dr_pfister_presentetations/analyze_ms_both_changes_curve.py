"""Audit the nine diagnostic MS curve ledgers and compare with source points."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import binomtest

from run_full_v2_curve import source_rows


ROOT = Path(__file__).resolve().parent / "results"
CAMPAIGN = ROOT / "ms_both_changes_curve"
BASELINE = ROOT / "full_v2_curves"
POINTS = (
    ("b1", "0060", .06), ("b1", "0080", .08),
    ("b1", "0100", .10), ("b1", "0120", .12),
    ("b1", "0140", .14), ("double_gross", "0060", .06),
    ("double_gross", "0080", .08), ("double_gross", "0100", .10),
    ("double_gross", "0120", .12),
)


def _audit_new(folder: Path) -> tuple[dict, list[dict]]:
    summary = json.loads((folder / "summary.json").read_text())
    digest = hashlib.sha256()
    records = []
    with gzip.open(folder / summary["event_ledger"], "rb") as handle:
        for raw in handle:
            digest.update(raw)
            records.append(json.loads(raw))
    if digest.hexdigest() != summary["event_ledger_uncompressed_sha256"]:
        raise ValueError(f"ledger SHA-256 mismatch: {folder}")
    counts = summary["counts"]
    if len(records) != counts["shots"] or [r["shot"] for r in records] != list(range(len(records))):
        raise ValueError(f"shot sequence or denominator mismatch: {folder}")
    for key in ("type_i", "type_ii", "exact_success", "stabilizer_success"):
        if sum(record[key] for record in records) != counts[key]:
            raise ValueError(f"{key} count mismatch: {folder}")
    if sum(record["iterations"] for record in records) != counts["total_iterations"]:
        raise ValueError(f"iteration count mismatch: {folder}")
    if sum(counts[key] for key in
           ("type_i", "type_ii", "exact_success", "stabilizer_success")) != len(records):
        raise ValueError(f"outcome partition mismatch: {folder}")
    if summary["failures"] != counts["type_i"] + counts["type_ii"]:
        raise ValueError(f"failure count mismatch: {folder}")
    return summary, records


def _baseline_prefix(folder: Path, shots: int) -> tuple[dict, list[dict]]:
    summary = json.loads((folder / "summary.json").read_text())
    records = []
    with gzip.open(folder / "events.jsonl.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["shot"] >= shots:
                break
            if record["arm"] == "bp4_vanilla_ms_q8":
                records.append(record)
    if len(records) != shots or [r["shot"] for r in records] != list(range(shots)):
        raise ValueError(f"baseline prefix incomplete: {folder}")
    return summary, records


def _fails(record: dict) -> bool:
    return bool(record["type_i"] or record["type_ii"])


def main() -> None:
    rows = []
    for code, label, p in POINTS:
        folder = CAMPAIGN / f"{code}_p{label}"
        summary, new = _audit_new(folder)
        base_summary, old = _baseline_prefix(BASELINE / f"{code}_p{label}", len(new))
        if summary["code"] != code or abs(summary["physical_p"] - p) > 1e-12:
            raise ValueError(f"point identity mismatch: {folder}")
        if summary["seed"] != base_summary["seed"]:
            raise ValueError(f"seed mismatch: {folder}")
        reference = source_rows(code, p)["bp4_vanilla_ms"]
        source_rate = float(reference["reported_ler"])
        if summary["source_ler"] != source_rate:
            raise ValueError(f"source rate mismatch: {folder}")
        for candidate, baseline in zip(new, old):
            if candidate["error_sha256"] != baseline["error_sha256"]:
                raise ValueError(f"sampled-error hash mismatch: {folder}, shot {candidate['shot']}")
        failures = summary["failures"]
        n = len(new)
        ci = binomtest(failures, n).proportion_ci(.95, method="exact")
        if abs(summary["lower_95"] - ci.low) > 1e-12 or abs(summary["upper_95"] - ci.high) > 1e-12:
            raise ValueError(f"confidence interval mismatch: {folder}")
        rescues = sum(_fails(a) and not _fails(b) for a, b in zip(old, new))
        losses = sum(not _fails(a) and _fails(b) for a, b in zip(old, new))
        old_failures = sum(_fails(record) for record in old)
        if old_failures - rescues + losses != failures:
            raise ValueError(f"paired outcome accounting mismatch: {folder}")
        rows.append({
            "code": code, "p": p, "source_ler": source_rate,
            "local_failures": failures, "shots": n, "local_ler": failures / n,
            "lower_95": ci.low, "upper_95": ci.high,
            "source_inside_local_95": ci.low <= source_rate <= ci.high,
            "type_i": summary["counts"]["type_i"],
            "type_ii": summary["counts"]["type_ii"],
            "mean_iterations": summary["mean_iterations"],
            "original_q8_prefix_failures": old_failures,
            "rescues": rescues, "losses": losses,
            "seed": summary["seed"],
        })

    with (CAMPAIGN / "comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    holdout_folder = CAMPAIGN / "double_gross_p0060_holdout_n50000_seed20261230"
    holdout, holdout_records = _audit_new(holdout_folder)
    if (holdout["code"] != "double_gross" or holdout["physical_p"] != .06
            or holdout["seed"] != 20261230 or len(holdout_records) != 50_000):
        raise ValueError("independent holdout identity mismatch")
    if holdout["seed"] == next(r["seed"] for r in rows if r["code"] == "double_gross" and r["p"] == .06):
        raise ValueError("holdout reused the original point seed")
    holdout_result = {
        "code": holdout["code"], "p": holdout["physical_p"],
        "seed": holdout["seed"], "failures": holdout["failures"],
        "shots": holdout["counts"]["shots"], "ler": holdout["ler"],
        "lower_95": holdout["lower_95"], "upper_95": holdout["upper_95"],
        "source_ler": holdout["source_ler"],
        "source_inside_local_95": holdout["lower_95"] <= holdout["source_ler"] <= holdout["upper_95"],
    }
    (CAMPAIGN / "analysis.json").write_text(json.dumps({
        "schema": "ms-both-changes-curve-analysis-v1",
        "audited_points": len(rows), "rows": rows,
        "independent_holdout": holdout_result,
    }, indent=2) + "\n")
    report = [
        "# BP4 min-sum with both numerical changes: full source-point check", "",
        "All nine reported vanilla BP4 MS `(code,p)` positions were run with 10,000",
        "shots each, using the existing full-v2 point seed and `p0=p`. The hybrid",
        "retains Q8 scalar commutation and check messages at scale 16, while",
        "keeping the three identity-referenced V2C coordinates unbounded and",
        "forming the complete log-sum-exp difference before scalar quantization.",
        "It is not the source's proven Q8 implementation. Its explicit policy",
        "is in `../../decoders/bp4_ms_both_changes_diagnostic.json`.", "",
        "Every new per-shot ledger SHA-256, shot sequence, outcome partition,",
        "failure count, and confidence interval was independently checked.",
        "Each error hash matched the corresponding original Q8 run's prefix.", "",
        "| Code | p | Reference LER | Hybrid failures/N | Hybrid LER [exact 95% CI] | Reference inside CI? | Original Q8 failures/10k | Rescues/losses | Mean iterations |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for r in rows:
        report.append(
            f"| {r['code']} | {r['p']:.3f} | {r['source_ler']:.6g} | "
            f"{r['local_failures']}/{r['shots']} | {r['local_ler']:.6g} "
            f"[{r['lower_95']:.3g}, {r['upper_95']:.3g}] | "
            f"{'yes' if r['source_inside_local_95'] else 'no'} | "
            f"{r['original_q8_prefix_failures']}/{r['shots']} | "
            f"{r['rescues']}/{r['losses']} | {r['mean_iterations']:.2f} |"
        )
    report += [
        "", "## Independent low-p holdout", "",
        f"The weakest 10,000-shot comparison, double-Gross p=.06, was checked",
        f"on 50,000 independent errors (seed {holdout['seed']}). The hybrid had",
        f"{holdout['failures']}/50,000 failures = {holdout['ler']:.5g}, with an exact",
        f"95% interval [{holdout['lower_95']:.5g}, {holdout['upper_95']:.5g}].",
        f"The reference point estimate {holdout['source_ler']:.5g} is below this",
        "local interval. This leaves a residual low-p discrepancy despite the",
        "strong overall improvement. The source's own sampling uncertainty is",
        "unknown, so this does not establish a formal two-sample difference.",
        "", "The source denominators are unknown. Inclusion in a local interval",
        "is a descriptive proximity check, not a formal two-sample test.",
        "A zero observed rate is not a zero true rate. This hybrid changes the",
        "internal numerical policy and should not be labeled source-faithful Q8.", "",
    ]
    (CAMPAIGN / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), sharey=True,
                             constrained_layout=True)
    for axis, code, title in zip(axes, ("b1", "double_gross"),
                                  ("B1 [[882,24]]", "double-Gross [[288,12,18]]")):
        subset = [r for r in rows if r["code"] == code]
        xs = [r["p"] for r in subset]
        axis.plot(xs, [r["source_ler"] for r in subset],
                  "s--", color="#777777", label="reference MS", linewidth=1.4)
        axis.errorbar(xs, [r["local_ler"] for r in subset],
                      yerr=[[r["local_ler"] - r["lower_95"] for r in subset],
                            [r["upper_95"] - r["local_ler"] for r in subset]],
                      fmt="o-", color="#d55e00", capsize=2.5,
                      label="hybrid MS, 10k shots", linewidth=1.5)
        axis.plot(xs, [r["original_q8_prefix_failures"] / r["shots"] for r in subset],
                  "x:", color="#aaaaaa", label="original Q8 MS, same errors", linewidth=1.2)
        axis.set(title=title, xlabel="Depolarizing probability p", yscale="log", ylim=(1e-3, 1.2))
        axis.grid(True, which="both", alpha=.20)
    axes[0].set_ylabel("Block logical error rate")
    axes[1].errorbar([.06], [holdout["ler"]],
                     yerr=[[holdout["ler"] - holdout["lower_95"]],
                           [holdout["upper_95"] - holdout["ler"]]],
                     fmt="D", markerfacecolor="white", markeredgecolor="#d55e00",
                     ecolor="#d55e00", capsize=2.5, markersize=6,
                     label="independent 50k holdout")
    axes[1].legend(loc="upper left", fontsize=7.5)
    fig.savefig(CAMPAIGN / "curve_comparison.png", dpi=180)
    fig.savefig(CAMPAIGN / "curve_comparison.pdf",
                metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    print("AUDIT PASS:", len(rows), "points and independent holdout")
    for r in rows:
        print(r["code"], r["p"], f"{r['local_failures']}/{r['shots']}",
              "source", r["source_ler"],
              "inside_ci", r["source_inside_local_95"])
    print("holdout", holdout_result)


if __name__ == "__main__":
    main()
