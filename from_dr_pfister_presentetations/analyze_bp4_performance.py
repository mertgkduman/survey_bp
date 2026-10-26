"""Audit matched-shot BP4 investigation ledgers and native C++ replay.

Usage: PYTHONPATH=src .venv/bin/python from_dr_pfister_presentetations/analyze_bp4_performance.py
"""

from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent / "results/performance_investigation"


def audit_run(run: Path) -> tuple[dict, dict[str, dict[int, dict]]]:
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    ledger_bytes = (run / summary["event_ledger"]).read_bytes()
    assert hashlib.sha256(ledger_bytes).hexdigest() == summary["event_ledger_sha256"], run
    by_arm: dict[str, dict[int, dict]] = defaultdict(dict)
    hashes: dict[int, str] = {}
    for line in ledger_bytes.splitlines():
        event = json.loads(line)
        arm, shot = event["arm"], event["shot"]
        assert 0 <= shot < summary["shots"] and shot not in by_arm[arm]
        assert shot not in hashes or hashes[shot] == event["error_sha256"]
        hashes[shot] = event["error_sha256"]
        assert event["failed"] == (not event["valid_syndrome"] or event["logical_failure"])
        assert not event["logical_failure"] or event["valid_syndrome"]
        by_arm[arm][shot] = event
    assert set(by_arm) == {item["id"] for item in summary["configs"]}
    assert len(hashes) == summary["shots"]
    for arm, events in by_arm.items():
        assert len(events) == summary["shots"]
        c = summary["counts"][arm]
        assert c["failures"] == sum(e["failed"] for e in events.values())
        assert c["invalid_syndrome"] == sum(not e["valid_syndrome"] for e in events.values())
        assert c["logical_failures_with_valid_syndrome"] == sum(e["logical_failure"] for e in events.values())
    return summary, by_arm


def paired(a: dict[int, dict], b: dict[int, dict]) -> dict:
    """Return a-to-b improvement: rescues are a failures and b successes."""
    assert a.keys() == b.keys()
    rescues = sum(a[i]["failed"] and not b[i]["failed"] for i in a)
    losses = sum(not a[i]["failed"] and b[i]["failed"] for i in a)
    return {"rescues": rescues, "losses": losses,
            "two_sided_exact_mcnemar_p": binomtest(rescues, rescues + losses, 0.5).pvalue
            if rescues + losses else 1.0}


def main() -> None:
    rows = []
    comparisons = []
    audited = {}
    for run in sorted(ROOT.iterdir()):
        if not run.is_dir() or not (run / "summary.json").is_file():
            continue
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        if "configs" not in summary:
            ledger = (run / summary["event_ledger"]).read_bytes()
            assert hashlib.sha256(ledger).hexdigest() == summary["event_ledger_sha256"]
            public = [json.loads(line) for line in ledger.splitlines()]
            assert len(public) == summary["shots"]
            assert sum(not e["same_candidate"] for e in public) == summary["candidate_disagreements"]
            assert sum(e["public_failed"] != e["compiled_failed"] for e in public) == summary["outcome_disagreements"]
            continue  # public-vs-compiled candidate audit has a separate schema
        summary, events = audit_run(run)
        audited[run.name] = (summary, events)
        n = summary["shots"]
        for arm, shots in events.items():
            failures = summary["counts"][arm]["failures"]
            ci = binomtest(failures, n).proportion_ci(method="exact")
            rows.append({"run": run.name, "code": summary["code"], "p": summary["physical_p"],
                         "seed": summary["seed"], "arm": arm, "failures": failures, "shots": n,
                         "ler": failures / n, "ci95_low": ci.low, "ci95_high": ci.high,
                         "invalid_syndrome": summary["counts"][arm]["invalid_syndrome"],
                         "valid_syndrome_logical": summary["counts"][arm]["logical_failures_with_valid_syndrome"],
                         "mean_iterations": summary["counts"][arm]["iterations"] / n})
        if "binary_oms" in events:
            for arm in events:
                if arm != "binary_oms":
                    comparisons.append({"run": run.name, "reference": "binary_oms", "new": arm,
                                        **paired(events["binary_oms"], events[arm])})
        minsum_arms = [item["id"] for item in summary["configs"] if item.get("min_sum") is True]
        if len(minsum_arms) == 2:
            comparisons.append({"run": run.name, "reference": minsum_arms[0], "new": minsum_arms[1],
                                **paired(events[minsum_arms[0]], events[minsum_arms[1]])})
        if summary["code"] == "miao_toric_d4":
            paper = events["paper_like_f64_limit60_p10"]
            canonical = events["canonical_f64_limit25_p10"]
            native_path = run / "native_raw.jsonl"
            native = [json.loads(line) for line in native_path.read_text(encoding="utf-8").splitlines()]
            assert len(native) == n
            for index, record in enumerate(native):
                assert record["shot"] == index
                assert record["success"] == (not paper[index]["failed"])
                assert record["valid_syndrome"] == paper[index]["valid_syndrome"]
                assert paper[index]["failed"] == canonical[index]["failed"]
                assert paper[index]["valid_syndrome"] == canonical[index]["valid_syndrome"]
            input_manifest = json.loads((run / "native_input_manifest.json").read_text(encoding="utf-8"))
            assert hashlib.sha256((run / input_manifest["input"]).read_bytes()).hexdigest() == input_manifest["input_sha256"]
            assert input_manifest["shots"] == n
            comparisons.append({"run": run.name, "reference": "native_cpp", "new": "paper_like_f64_limit60_p10",
                                "rescues": 0, "losses": 0, "two_sided_exact_mcnemar_p": 1.0})

    cross_runs = [
        ("b1_confirmation_p010_n300_seed20261106", "binary_oms",
         "b1_float_p010_n300_seed20261106", ("f64_p10", "f64_p20")),
        *[("gross_holdout_p008_n1000_seed20261031", arm,
           "gross_independent_p008_n1000_seed20261031", (arm,))
          for arm in ("binary_oms", "q8_s16_d0_p08", "q8_s4_d01_p08", "q8_s4_d02_p20")],
        *[("b1_transfer_p010_n200_seed20261101", arm,
           "b1_independent_p010_n100_seed20261101", (arm,))
          for arm in ("binary_oms", "q8_s16_d0_p10", "q8_s4_d01_p10", "q8_s4_d02_p20")],
        ("b1_transfer_p010_n200_seed20261101", "q8_s16_d0_p10",
         "b1_minsum_p010_n200_seed20261101", ("q8_ms_s16_d0_p10",)),
        ("b1_transfer_p010_n200_seed20261101", "q8_s4_d01_p10",
         "b1_minsum_p010_n200_seed20261101", ("q8_ms_s4_d01_p10",)),
        ("gross_holdout_p008_n1000_seed20261031", "q8_s16_d0_p08",
         "gross_minsum_p008_n1000_seed20261031", ("q8_ms_s16_d0_p08",)),
        ("gross_holdout_p008_n1000_seed20261031", "q8_s4_d01_p08",
         "gross_minsum_p008_n1000_seed20261031", ("q8_ms_s4_d01_p08",)),
    ]
    for reference_run, reference_arm, new_run, new_arms in cross_runs:
        if reference_run not in audited or new_run not in audited:
            continue
        ref_summary, ref_events = audited[reference_run]
        new_summary, new_events = audited[new_run]
        assert (ref_summary["code"], ref_summary["physical_p"], ref_summary["seed"]) == (
            new_summary["code"], new_summary["physical_p"], new_summary["seed"])
        assert ref_summary["shots"] >= new_summary["shots"]
        for new_arm in new_arms:
            fresh = new_events[new_arm]
            reference = {i: ref_events[reference_arm][i] for i in fresh}
            assert all(reference[i]["error_sha256"] == fresh[i]["error_sha256"] for i in reference)
            comparisons.append({"run": f"{reference_run} vs {new_run}", "reference": reference_arm,
                                "new": new_arm, **paired(reference, fresh)})

    with (ROOT / "audited_rates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with (ROOT / "paired_comparisons.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparisons[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparisons)
    plot_confirmation(rows)
    plot_minsum_comparison(rows)
    print(f"Audited {len(rows)} arms, {len(comparisons)} paired comparisons; native replay exact match.")


def plot_confirmation(rows: list[dict]) -> None:
    """Keep local confirmation intervals visibly distinct from slide points."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [
        ("b1_confirmation_p010_n300_seed20261106", "B1, p = 0.10",
         [("binary_oms", "binary OMS"), ("q8_s4_d01_p10", "Q8 BP4, slide-like"),
          ("q8_s4_d03_p20", "Q8 BP4, d=.3 p₀=.2"),
          ("q8_s4_d04_p20", "Q8 BP4, d=.4 p₀=.2")], .04571, .00032),
        ("gross_confirmation_p008_n3000_seed20261105", "double-Gross, p = 0.08",
         [("binary_oms", "binary OMS"), ("q8_s4_d01_p08", "Q8 BP4, slide-like"),
          ("q8_s4_d02_p20", "Q8 BP4, d=.2 p₀=.2")], .03153, .00077),
    ]
    if any(not (ROOT / name / "summary.json").is_file() for name, *_ in panels):
        return
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for ax, (run, title, arms, slide_binary, slide_bp4) in zip(axes, panels, strict=True):
        data = {r["arm"]: r for r in rows if r["run"] == run}
        for x, (arm, _) in enumerate(arms):
            record = data[arm]
            ax.errorbar(x, record["ler"], yerr=[[record["ler"] - record["ci95_low"]],
                                                  [record["ci95_high"] - record["ler"]]],
                        fmt="o", color="#17365d" if arm == "binary_oms" else "#c04a16",
                        capsize=3, markersize=6, zorder=3)
            ax.annotate(f'{record["failures"]}/{record["shots"]}', (x, record["ci95_high"]),
                        xytext=(0, 5), textcoords="offset points", ha="center", fontsize=8)
        ax.axhline(slide_binary, color="#17365d", linestyle=":", linewidth=1.3,
                   label="presentation binary")
        ax.axhline(slide_bp4, color="#c04a16", linestyle="--", linewidth=1.3,
                   label="presentation tuned BP4")
        ax.set(xticks=range(len(arms)), xticklabels=[label for _, label in arms],
               xlim=(-.55, len(arms) - .45), title=title, ylabel="Logical error rate",
               yscale="log", ylim=(1e-4, 1))
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .90),
               fontsize=9, ncol=2, frameon=False)
    fig.suptitle("Fresh paired confirmations; error bars are exact 95% binomial intervals",
                 fontsize=12, y=.99)
    fig.subplots_adjust(left=.09, right=.98, bottom=.28, top=.75, wspace=.25)
    for ext in ("png", "svg"):
        fig.savefig(ROOT / f"confirmation_comparison.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    svg = ROOT / "confirmation_comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
                   + "\n", encoding="utf-8")


def plot_minsum_comparison(rows: list[dict]) -> None:
    """Plot matched SP/MS arms with their observed denominators and intervals."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [
        ("B1, p = 0.10", "b1_transfer_p010_n200_seed20261101",
         "b1_minsum_p010_n200_seed20261101",
         ("q8_s16_d0_p10", "q8_ms_s16_d0_p10", "q8_s4_d01_p10", "q8_ms_s4_d01_p10")),
        ("double-Gross, p = 0.08", "gross_holdout_p008_n1000_seed20261031",
         "gross_minsum_p008_n1000_seed20261031",
         ("q8_s16_d0_p08", "q8_ms_s16_d0_p08", "q8_s4_d01_p08", "q8_ms_s4_d01_p08")),
    ]
    if any(not (ROOT / minsum_run / "summary.json").is_file() for _, _, minsum_run, _ in panels):
        return
    lookup = {(row["run"], row["arm"]): row for row in rows}
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.7))
    labels = ("SP vanilla", "MS vanilla", "SP tuned", "MS tuned")
    for ax, (title, sp_run, ms_run, arms) in zip(axes, panels, strict=True):
        for index, arm in enumerate(arms):
            row = lookup[(sp_run if index % 2 == 0 else ms_run, arm)]
            rate = row["ler"]
            color = "#315a85" if index % 2 == 0 else "#c04a16"
            if row["failures"] == 0:
                position = 1.0 - .05 ** (1.0 / row["shots"])
                ax.plot(index, position, marker="v", markerfacecolor="white", markeredgecolor=color)
            else:
                position = row["ci95_high"]
                ax.errorbar(index, rate,
                            yerr=[[rate - row["ci95_low"]], [row["ci95_high"] - rate]],
                            fmt="o", color=color, capsize=3, markersize=7)
            ax.annotate(f'{row["failures"]}/{row["shots"]}', (index, position),
                        xytext=(0, 5), textcoords="offset points", ha="center", fontsize=8)
        ax.set(title=title, ylabel="Logical error rate", yscale="log", ylim=(.001, 2),
               xlim=(-.6, 3.6), xticks=range(4), xticklabels=labels)
        ax.grid(axis="y", alpha=.2)
    fig.suptitle("BP4 sum-product and min-sum on identical errors; exact 95% intervals", fontsize=11)
    fig.subplots_adjust(left=.09, right=.98, bottom=.20, top=.79, wspace=.25)
    for ext in ("png", "svg"):
        fig.savefig(ROOT / f"minsum_vs_sumproduct.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    svg = ROOT / "minsum_vs_sumproduct.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
                   + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
