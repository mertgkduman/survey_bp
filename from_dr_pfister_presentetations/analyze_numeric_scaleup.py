"""Audit paired ledgers and plot the BP numerical-policy scale-up."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "numerical_scaleup"
SOURCE = ROOT / "results" / "source_curves.csv"


def _load(path: Path) -> tuple[dict, dict[str, list[dict]]]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    payload = (path.parent / summary["event_ledger"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != summary["event_ledger_sha256"]:
        raise ValueError(f"event ledger digest mismatch: {path}")
    by_arm: dict[str, list[dict]] = {}
    for line in payload.splitlines():
        record = json.loads(line)
        by_arm.setdefault(record["arm"], []).append(record)
    n = summary["shots"]
    hashes = None
    for arm, records in by_arm.items():
        if len(records) != n or [r["shot"] for r in records] != list(range(n)):
            raise ValueError(f"missing or reordered shots: {path}, {arm}")
        current = [r["error_sha256"] for r in records]
        if hashes is not None and hashes != current:
            raise ValueError(f"arms do not share errors: {path}")
        hashes = current
        counts = summary["counts"][arm]
        for key in ("failed", "type_i", "type_ii", "exact_success", "stabilizer_success"):
            expected = counts["failures" if key == "failed" else key]
            if sum(bool(r[key]) for r in records) != expected:
                raise ValueError(f"count disagrees with ledger: {path}, {arm}, {key}")
        if sum(counts[k] for k in ("type_i", "type_ii", "exact_success", "stabilizer_success")) != n:
            raise ValueError(f"outcomes do not partition shots: {path}, {arm}")
    return summary, by_arm


def main() -> None:
    points = []
    pair_rows = []
    for path in sorted(RESULTS.glob("*/summary.json")):
        summary, arms = _load(path)
        n = summary["shots"]
        for arm, records in arms.items():
            failures = summary["counts"][arm]["failures"]
            ci = binomtest(failures, n).proportion_ci(method="exact")
            work = np.asarray([r["bp4_equivalent_work"] for r in records], dtype=float)
            points.append({
                "run": path.parent.name, "status": summary["status"], "code": summary["code"],
                "p": summary["physical_p"], "shots": n, "arm": arm,
                "failures": failures, "type_i": summary["counts"][arm]["type_i"],
                "type_ii": summary["counts"][arm]["type_ii"],
                "ler": failures/n, "ci_low": ci.low, "ci_high": ci.high,
                "mean_work": float(np.mean(work)), "p99_work": float(np.percentile(work, 99)),
                "p999_work": float(np.percentile(work, 99.9)),
            })
        chosen = next((name for name in (
            "product_e10_d01", "binary_product_e10_d01", "bp4_v2_product_d01_p0_010"
        ) if name in arms), None)
        if chosen:
            base = [bool(r["failed"]) for r in arms[chosen]]
            for other, records in arms.items():
                if other == chosen:
                    continue
                comparison = [bool(r["failed"]) for r in records]
                rescues = sum(a and not b for a, b in zip(comparison, base, strict=True))
                losses = sum(not a and b for a, b in zip(comparison, base, strict=True))
                discordant = rescues + losses
                pair_rows.append({
                    "run": path.parent.name, "chosen": chosen, "other": other,
                    "rescues": rescues, "losses": losses,
                    "mcnemar_exact_p": binomtest(rescues, discordant, .5).pvalue if discordant else 1.0,
                })
    for name, rows in (("points.csv", points), ("pairs.csv", pair_rows)):
        if not rows:
            continue
        with (RESULTS / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    source = list(csv.DictReader(SOURCE.open(encoding="utf-8")))
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4), sharey=True)
    for ax, code, label in zip(axes, ("b1", "double_gross"), ("B1 [[882,24]]", "double-Gross [[288,12,18]]"), strict=True):
        source_code = "B1_882_24" if code == "b1" else "double_Gross_288_12_18"
        target = [(float(r["p"]), float(r["reported_ler"])) for r in source
                  if r["code"] == source_code and r["decoder"] == "bp4_tuned_sp" and r["point_type"] == "observed"]
        ax.plot(*zip(*target), color="black", marker="o", markersize=4, label="presentation tuned BP4")
        bounds = [(float(r["p"]), float(r["reported_ler"])) for r in source
                  if r["code"] == source_code and r["decoder"] == "bp4_tuned_sp"
                  and r["point_type"] == "upper_95_one_sided"]
        if bounds:
            ax.scatter(*zip(*bounds), color="black", marker="v", facecolors="none", s=48,
                       label="presentation zero-failure bound")
        selected = sorted((r for r in points if r["status"] == "heldout" and r["code"] == code
                           and r["arm"] == "product_e10_d01"), key=lambda r: r["p"])
        if selected:
            x = [r["p"] for r in selected]
            y = [max(r["ler"], .5/r["shots"]) for r in selected]
            ax.errorbar(x, y, yerr=[[max(0, v-r["ci_low"]) for v, r in zip(y, selected, strict=True)],
                                    [max(0, r["ci_high"]-v) for v, r in zip(y, selected, strict=True)]],
                        fmt="D", color="#0072B2", capsize=3, label="canonical v2 candidate (95% CI)")
        ax.set(title=label, xlabel="Depolarizing probability p", yscale="log", ylim=(5e-6, 1), xlim=(.055,.145) if code=="b1" else (.035,.125))
        ax.grid(True, which="both", alpha=.2)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Block logical error rate")
    fig.tight_layout()
    fig.savefig(RESULTS / "bp4_heldout_vs_presentation.png", dpi=180)
    fig.savefig(RESULTS / "bp4_heldout_vs_presentation.pdf", metadata={
        "Creator": "bp numeric scale-up", "CreationDate": None, "ModDate": None,
    })
    plt.close(fig)
    print(f"Audited {len(points)} arm-runs and {len(pair_rows)} paired comparisons")


if __name__ == "__main__":
    main()
