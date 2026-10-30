"""Verify retained shots and compare each non-OSD source point with exact binomial intervals."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta
from importance_assess import verified_importance_runs
from ledger_io import open_event_ledger

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = json.loads((ROOT / "source_points.json").read_text())
PRIOR_QBP = REPO / "data/reproductions/yao-2312-10950-vanilla/results/comparison.csv"
LEGACY_RUNNER_SHA256 = "4b4912da054fb67f69c3238cca036a3e449c7e3e5a0469e10ae185fd1fc61c76"  # commit 50d6371
RARE_SHARDS_PLAN = ROOT / "results/completion-rare-shards-plan.json"


def exact_interval(failures: int, shots: int) -> tuple[float, float]:
    if not 0 <= failures <= shots or shots < 1:
        raise ValueError("invalid binomial count")
    return (0.0 if failures == 0 else float(beta.ppf(0.025, failures, shots - failures + 1)),
            1.0 if failures == shots else float(beta.ppf(0.975, failures + 1, shots - failures)))


def run_interval(item: dict) -> tuple[float, float]:
    failures, shots = item["failures"], item["shots"]
    if item.get("stop_reason") == "target_failures":
        # Invert the negative-binomial stopping distribution at a fixed failure count.
        return (float(beta.ppf(0.025, failures, shots - failures + 1)),
                1.0 if failures == shots else float(beta.ppf(0.975, failures, shots - failures)))
    return exact_interval(failures, shots)


def aggregate_fixed_shards(plan: dict, verified: dict[str, dict]) -> dict | None:
    """Combine only a complete, disjoint, individually audited iid plan."""
    if plan["schema"] != "yao-completion-rare-shards-plan-v1":
        raise ValueError("unexpected rare-shard plan schema")
    jobs = sorted(plan["jobs"], key=lambda item: item["start_shot"])
    if any(Path(job["output"]).name not in verified for job in jobs):
        return None
    if not jobs or jobs[0]["start_shot"] != 0:
        raise ValueError("rare-shard plan must start at shot zero")
    reference = (jobs[0]["code"], jobs[0]["method"], jobs[0]["p"], jobs[0]["seed"])
    counts = {key: 0 for key in verified[Path(jobs[0]["output"]).name]["counts"]}
    next_shot = 0
    for job in jobs:
        if (job["code"], job["method"], job["p"], job["seed"]) != reference:
            raise ValueError("rare-shard policy/seed mismatch")
        if job["start_shot"] != next_shot or job["target_failures"] is not None:
            raise ValueError("rare-shard plan has overlapping/gapped or nonfixed shots")
        item = verified[Path(job["output"]).name]
        if (item["code"], item["method"], item["physical_p"], item["seed"],
                item["start_shot"], item["shots"], item["stop_reason"]) != (
                job["code"], job["method"], job["p"], job["seed"],
                job["start_shot"], job["max_shots"], "fixed_shots"):
            raise ValueError("rare-shard manifest/summary differs from plan")
        if set(item["counts"]) != set(counts):
            raise ValueError("rare-shard count fields differ")
        for key in counts:
            counts[key] += item["counts"][key]
        next_shot += item["shots"]
    if next_shot != plan["total_fixed_shots"]:
        raise ValueError("rare-shard shot total differs from plan")
    return {"code": reference[0], "method": reference[1], "physical_p": reference[2],
            "shots": next_shot, "failures": counts["type_i"] + counts["type_ii"],
            "counts": counts, "stop_reason": "fixed_shots",
            "evidence_tier": "direct_shard_aggregate",
            "evidence_path": str(RARE_SHARDS_PLAN.relative_to(REPO))}


def verified_runs() -> dict[tuple[str, str, str], dict]:
    selected = {}
    rare_shards = {}
    rare_plan = json.loads(RARE_SHARDS_PLAN.read_text()) if RARE_SHARDS_PLAN.exists() else None
    rare_plan_ready = (rare_plan is not None and all(
        (REPO / job["output"] / "summary.json").exists() for job in rare_plan["jobs"]))
    for path in sorted((ROOT / "results").glob("*/summary.json")):
        if path.parent.name.startswith("completion-rare-shard-") and not rare_plan_ready:
            continue  # A partial fixed-shot plan cannot produce a curve estimate.
        summary = json.loads(path.read_text())
        if summary.get("schema") != "yao-non-osd-summary-v1":
            continue
        manifest_path = path.with_name("manifest.json")
        ledger_path = path.with_name("events.jsonl")
        if sha256(manifest_path.read_bytes()).hexdigest() != summary["manifest_sha256"]:
            raise ValueError(f"manifest mismatch: {path}")
        manifest = json.loads(manifest_path.read_text())
        runner_name = str((ROOT / "run_point.py").relative_to(REPO))
        if manifest["source_files_sha256"].get(runner_name) not in {
            sha256((ROOT / "run_point.py").read_bytes()).hexdigest(), LEGACY_RUNNER_SHA256,
        }:
            continue  # Keep old smoke evidence, but do not compare a superseded runner.
        digest = sha256()
        seen = 0
        counts = summary["counts"]
        total = {key: 0 for key in counts}
        fixations_sq = 0
        with open_event_ledger(ledger_path) as ledger:
            for raw in ledger:
                digest.update(raw)
                event = json.loads(raw)
                if event["shot"] != summary["start_shot"] + seen:
                    raise ValueError(f"shot sequence mismatch: {path}")
                seen += 1
                for key in total:
                    total[key] += int(event["outcome"][key])
                fixations_sq += int(event["outcome"]["fixations"]) ** 2
        if digest.hexdigest() != summary["events_sha256"] or seen != summary["shots"]:
            raise ValueError(f"ledger hash/count mismatch: {path}")
        if total != counts:
            raise ValueError(f"outcome count mismatch: {path}")
        if counts["type_i"] + counts["type_ii"] != summary["failures"]:
            raise ValueError(f"failure count mismatch: {path}")
        if sum(counts[key] for key in ("type_i", "type_ii", "exact_success", "stabilizer_success")) != summary["shots"]:
            raise ValueError(f"outcome partition mismatch: {path}")
        summary["fixations_se"] = (math.sqrt(max(0.0, (fixations_sq - counts["fixations"]**2 / seen) / (seen-1)) / seen)
                                   if seen > 1 else None)
        summary["evidence_path"] = str(path.relative_to(REPO))
        summary["evidence_tier"] = ("interrupted_prefix" if summary["stop_reason"] == "externally_interrupted_complete_prefix"
                                    else "pilot" if path.parent.name.startswith(("smoke", "pilot", "benchmark"))
                                    else "bounded_campaign")
        if path.parent.name.startswith("completion-rare-shard-"):
            rare_shards[path.parent.name] = summary
            continue
        key = (summary["code"], summary["method"], f'{summary["physical_p"]:.5f}')
        old = selected.get(key)
        if old is None or (summary["evidence_tier"] != "pilot", summary["shots"]) > (old["evidence_tier"] != "pilot", old["shots"]):
            selected[key] = summary
    if rare_plan_ready:
        aggregate = aggregate_fixed_shards(rare_plan, rare_shards)
        if aggregate is not None:
            key = (aggregate["code"], aggregate["method"], f'{aggregate["physical_p"]:.5f}')
            selected[key] = aggregate
    return selected


def prior_qbp_runs() -> dict[tuple[str, str, str], dict]:
    result = {}
    with PRIOR_QBP.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["arm"] != "bp4_v2" or row["complete"] != "True":
                continue
            result[(row["code"], "qbp", f'{float(row["p"]):.5f}')] = {
                "shots": int(row["shots"]), "failures": int(row["failures"]),
                "counts": {"type_i": int(row["type_i"]), "type_ii": int(row["type_ii"])},
                "mean_iterations": float(row["mean_bp4_equivalent_iterations"]),
                "mean_elapsed_ms": float(row["mean_decode_ms"]),
                "mean_fixations": 0.0,
                "evidence_path": str(PRIOR_QBP.relative_to(REPO)), "evidence_tier": "prior_vanilla_campaign",
            }
    return result


def build_rows() -> list[dict]:
    runs = verified_runs()
    runs.update(prior_qbp_runs())
    importance = verified_importance_runs()
    rows = []
    for figure, body in SOURCE["figures"].items():
        for curve, points in body["curves"].items():
            if curve == "bp_si_external":
                continue
            for p, published in points.items():
                method = "bpgd_t100" if curve == "bpgd_t100_r882" else curve
                key = (body["code"], method, p)
                item = runs.get(key)
                imp = importance.get(key)
                use_importance = False
                if imp is not None and imp["raw_failures"] > 0:
                    direct_width = math.inf if item is None else run_interval(item)[1] - run_interval(item)[0]
                    importance_width = imp["ci95_high"] - imp["ci95_low"]
                    use_importance = (item is None or
                                      item["failures"] < 30 and imp["failure_ess"] >= 20 and importance_width < direct_width)
                if use_importance:
                    lo, hi = imp["ci95_low"], imp["ci95_high"]
                    inside = lo <= published <= hi
                    relative_halfwidth = math.inf if imp["rate"] == 0 else (hi-lo)/(2*imp["rate"])
                    if (not imp["stage_complete"] or imp["failure_ess"] < 100
                            or relative_halfwidth > .25):
                        status = "importance_preliminary"
                        reason = (f'Mixture importance sampling has effective weighted failure count '
                                  f'{imp["failure_ess"]:.1f}; stage complete={imp["stage_complete"]}; '
                                  'target is a complete stage, at least 100 ESS, and 25% relative half-width')
                    else:
                        status = "importance_95_contains_source" if inside else "importance_95_excludes_source"
                        reason = "Approximate weighted 95% interval; source Monte Carlo uncertainty not included"
                    selected = {"shots": imp["shots"], "failures": imp["raw_failures"],
                                "type_i": imp["raw_type_i"], "type_ii": imp["raw_type_ii"],
                                "mean_iterations": imp["mean_iterations"],
                                "mean_fixations": imp["mean_fixations"],
                                "mean_decode_ms": imp["mean_decode_ms"],
                                "local_rate": imp["rate"], "ci95_low": lo, "ci95_high": hi,
                                "zero_failure_upper_one_sided95": None,
                                "evidence_tier": "importance_sampling",
                                "evidence_path": ";".join(imp["evidence_paths"]),
                                "estimator": "mixture_importance"}
                elif item is None:
                    status = "pending"
                    reason = f"No completed local run; about {math.ceil(100 / published):,} shots expected for 100 failures at the source rate"
                    selected = {"shots": None, "failures": None, "type_i": None, "type_ii": None,
                                "mean_iterations": None, "mean_fixations": None, "mean_decode_ms": None,
                                "local_rate": None, "ci95_low": None, "ci95_high": None,
                                "zero_failure_upper_one_sided95": None,
                                "evidence_tier": None, "evidence_path": None, "estimator": None}
                else:
                    lo, hi = run_interval(item)
                    inside = lo <= published <= hi
                    if item["evidence_tier"] == "pilot":
                        status = "pilot_only"
                        reason = "Execution smoke or pilot; not a curve estimate"
                    elif item["evidence_tier"] == "interrupted_prefix":
                        status = "interrupted_prefix_contains_source" if inside else "interrupted_prefix_excludes_source"
                        reason = "Only complete flushed shots were recovered after external termination"
                    elif item["failures"] < 30:
                        status = "low_count_unresolved" if inside else "low_count_tension"
                        reason = f'Only {item["failures"]} local failures; source uncertainty also unavailable'
                    else:
                        status = "local_95_contains_source" if inside else "local_95_excludes_source"
                        reason = "Source rate inside local interval" if inside else "Source rate outside local interval; source trial count unavailable"
                    selected = {"shots": item["shots"], "failures": item["failures"],
                                "type_i": item["counts"]["type_i"], "type_ii": item["counts"]["type_ii"],
                                "mean_iterations": item.get("mean_iterations", item["counts"].get("iterations", 0) / item["shots"]),
                                "mean_fixations": item.get("mean_fixations", item["counts"].get("fixations", 0) / item["shots"]),
                                "mean_decode_ms": item.get("mean_elapsed_ms", item["counts"].get("elapsed_ns", 0) / item["shots"] / 1e6),
                                "local_rate": item["failures"] / item["shots"],
                                "ci95_low": lo, "ci95_high": hi,
                                "zero_failure_upper_one_sided95": (1.0 - 0.05 ** (1.0 / item["shots"])
                                                                  if item["failures"] == 0 else None),
                                "evidence_tier": item["evidence_tier"],
                                "evidence_path": item["evidence_path"], "estimator": "iid"}
                # Figure captions say the plotted BP/BPGD points were collected
                # until 100 errors; plotted decimals do not reveal exact N.
                source_shots_approx = round(100 / published)
                source_lo, source_hi = run_interval({"failures": 100, "shots": source_shots_approx,
                                                      "stop_reason": "target_failures"})
                if selected["ci95_low"] is None:
                    source_mc_compatibility = "unmeasured"
                elif status in {"importance_preliminary", "pilot_only", "low_count_unresolved",
                                "low_count_tension"}:
                    source_mc_compatibility = "not_assessed_low_precision"
                elif selected["ci95_high"] < source_lo or source_hi < selected["ci95_low"]:
                    source_mc_compatibility = "separated_95_intervals"
                else:
                    source_mc_compatibility = "overlapping_95_intervals"
                rows.append({"figure": int(figure), "code": body["code"], "curve": curve, "p": p,
                             "published_rate": published, **selected, "assessment": status,
                             "assessment_reason": reason,
                             "source_inferred_100_failure_shots": source_shots_approx,
                             "source_approx_ci95_low": source_lo,
                             "source_approx_ci95_high": source_hi,
                             "source_mc_compatibility": source_mc_compatibility,
                             "expected_shots_for_100_at_source_rate": math.ceil(100 / published),
                             "importance_shots": None if imp is None else imp["shots"],
                             "importance_stage": None if imp is None else imp["analysis_stage"],
                             "importance_stage_complete": None if imp is None else imp["stage_complete"],
                             "importance_planning_pilot_shots": None if imp is None else imp["planning_pilot_shots"],
                             "importance_raw_failures": None if imp is None else imp["raw_failures"],
                             "importance_failure_ess": None if imp is None else imp["failure_ess"],
                             "importance_rate": None if imp is None else imp["rate"],
                             "importance_ci95_low": None if imp is None else imp["ci95_low"],
                             "importance_ci95_high": None if imp is None else imp["ci95_high"]})
    return rows


def write_outputs() -> None:
    rows = build_rows()
    result = ROOT / "results"
    with (result / "comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(2, 4, figsize=(17, 8), layout="constrained")
    for axis, figure in zip(axes.flat, range(2, 9)):
        group = [row for row in rows if row["figure"] == figure]
        for curve in dict.fromkeys(row["curve"] for row in group):
            points = [row for row in group if row["curve"] == curve]
            axis.plot([float(row["p"]) for row in points], [row["published_rate"] for row in points],
                      marker=".", linewidth=1, label=f"source {curve}")
            local = [row for row in points if row["local_rate"] is not None]
            for estimator, marker in (("iid", "x"), ("mixture_importance", "o")):
                positive = [row for row in local if row["failures"] > 0 and row["estimator"] == estimator]
                if positive:
                    axis.errorbar([float(row["p"]) for row in positive], [row["local_rate"] for row in positive],
                                  yerr=([row["local_rate"] - row["ci95_low"] for row in positive],
                                        [row["ci95_high"] - row["local_rate"] for row in positive]),
                                  fmt=marker, markersize=4, capsize=2, linewidth=.7,
                                  label=f'{"local" if estimator == "iid" else "IS"} {curve}')
            zero = [row for row in local if row["failures"] == 0 and row["estimator"] == "iid"]
            if zero:
                axis.scatter([float(row["p"]) for row in zero], [row["zero_failure_upper_one_sided95"] for row in zero],
                             marker="v", facecolors="none", edgecolors="black", s=30,
                             label=f"95% upper bound {curve}")
        axis.set(title=f"Figure {figure}: {group[0]['code'].upper()}", xlabel="physical p", ylabel="block error rate", yscale="log")
        axis.grid(alpha=.2)
        axis.legend(fontsize=6, ncol=2)
    axes.flat[-1].axis("off")
    fig.savefig(result / "comparison.png", dpi=180)
    fig.savefig(result / "comparison.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    from collections import Counter
    statuses = Counter(row["assessment"] for row in rows)
    featured = [row for row in rows if row["p"] == "0.06000" and row["figure"] in (3, 5, 7, 8)
                and row["curve"] in ("bp", "bpgd_t10", "qbp")]
    runs = verified_runs()
    lines = ["# Yao BP/BPGD reproduction assessment", "",
             "Source: [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2).",
             "This comparison contains only BP and BPGD. Direct-run two-sided 95% intervals invert the negative-binomial distribution for runs stopped at a fixed failure count, or use Clopper–Pearson bounds for fixed/capped shot runs. Mixture importance-sampling (IS) intervals are approximate normal intervals using the weighted shot variance and are marked separately. Zero-failure triangles mark the exact one-sided 95% upper bound, about 3/N. Figure captions say source points were collected to 100 errors; approximate source intervals infer N=round(100/plotted rate), because exact denominators were not supplied. Interval overlap is descriptive, not a formal equivalence test.", "",
             "## Coverage", ""]
    lines.extend(f"- {key}: {count}" for key, count in sorted(statuses.items()))
    lines.extend(["", "## Rare-event estimator", "",
                  "For each IS shot, an iid error is drawn from 0.1 P_p + 0.9 P_q with q>p, decoded using the source p, and its failure indicator is weighted by P_p(error)/(0.1 P_p(error)+0.9 P_q(error)). The estimator averages these weighted indicators. The expected value is the ordinary iid error rate at p; the source simulation itself used direct iid shots. The assessor verifies the exact proposal draw and likelihood weight for every retained shot. Extension sizes are chosen from pilot data; the reported estimate uses only the latest independently fixed stage so the pilot does not enter its own adaptively sized follow-up. IS is promoted from preliminary only when that stage is complete, the effective weighted failure count reaches 100, and the approximate 95% relative half-width is at most 25%. This interval does not include uncertainty in the published point."])
    importance_progress = {}
    for row in rows:
        if row["importance_shots"] is not None:
            method = "bpgd_t100" if row["curve"] == "bpgd_t100_r882" else row["curve"]
            importance_progress[(row["code"], method, row["p"])] = row
    if importance_progress:
        lines.extend(["", "### IS progress by distinct decoder point", "",
                      "Raw failures are proposal-distribution failures. The effective weighted failure count (ESS) controls precision; an initial pilot with low ESS is not a completed reproduction.", "",
                      "| Code | Decoder | p | Stage | Source | IS rate | Raw failures/shots | Failure ESS |",
                      "|---|---|---:|---:|---:|---:|---:|---:|"])
        for (code, method, p), row in sorted(importance_progress.items()):
            lines.append(f'| {code.upper()} | {method} | {float(p):.2f} | {row["importance_stage"]} | {row["published_rate"]:.6g} | {row["importance_rate"]:.6g} | {row["importance_raw_failures"]}/{row["importance_shots"]} | {row["importance_failure_ess"]:.1f} |')
    lines.extend(["", "## Principal curve points", "",
                  "B1 T=10 uses Figure 3 below; Figure 4's conflicting T=10 targets remain separate in the CSV.", "",
                  "| Code | p | Source plain BP | Local plain BP | Source guided T=10 | Local guided T=10 |", "|---|---:|---:|---:|---:|---:|"])
    for figure, code, plain in ((3, "b1", "bp"), (5, "c2", "bp"), (7, "a5", "qbp"), (8, "b2", "qbp")):
        for p in sorted(SOURCE["figures"][str(figure)]["curves"][plain]):
            point = {(row["curve"]): row for row in rows if row["figure"] == figure and row["p"] == p}
            source_plain, source_guided = point[plain], point["bpgd_t10"]
            def local_label(row: dict) -> str:
                if row["local_rate"] is None:
                    return "—"
                if row["estimator"] == "mixture_importance":
                    return f'IS {row["local_rate"]:.4g} (N={row["shots"]}, ESS={row["importance_failure_ess"]:.1f})'
                return f'{row["failures"]}/{row["shots"]} ({row["local_rate"]:.4g})'
            lines.append(f'| {code.upper()} | {float(p):.2f} | {source_plain["published_rate"]:.5g} | {local_label(source_plain)} | {source_guided["published_rate"]:.5g} | {local_label(source_guided)} |')
    lines.extend(["", "## Representative p=0.06 points", "",
                  "| Figure | Code | Decoder | Source | Local estimate | Local 95% interval | Assessment |", "|---:|---|---|---:|---:|---:|---|"])
    for row in featured:
        local = "pending" if row["shots"] is None else (f'IS {row["local_rate"]:.5g} (N={row["shots"]}, ESS={row["importance_failure_ess"]:.1f})'
                                                      if row["estimator"] == "mixture_importance" else f'{row["failures"]}/{row["shots"]}')
        interval = "—" if row["shots"] is None else f'[{row["ci95_low"]:.5g}, {row["ci95_high"]:.5g}]'
        lines.append(f'| {row["figure"]} | {row["code"].upper()} | {row["curve"]} | {row["published_rate"]:.6g} | {local} | {interval} | {row["assessment"]} |')
    exclusions = [row for row in rows if row["assessment"] in {"local_95_excludes_source", "importance_95_excludes_source"}]
    separated = [row for row in rows if row["source_mc_compatibility"] == "separated_95_intervals"]
    if separated:
        unique = {(row["code"], row["curve"], row["p"]): row for row in separated}
        lines.extend(["", "## Source Monte Carlo discrepancies", "",
                      "The following distinct points have disjoint local and approximate source 95% intervals. The source intervals assume the caption's 100-failure stopping rule; exact source shot counts were not released. These are discrepancies to investigate, not proof of a particular implementation defect.", ""])
        for row in unique.values():
            lines.append(f'- {row["code"].upper()} {row["curve"]}, p={float(row["p"]):.2f}: '
                         f'local {row["local_rate"]:.6g}, source {row["published_rate"]:.6g}.')
    lines.extend(["", "## Points outside the local 95% interval", "",
                  "These are point-versus-interval flags, not formal two-sample discrepancy tests. The source interval below is approximate because its denominator is inferred from the caption's 100-failure rule and the rounded plotted rate. Figures repeating the same result are shown once.", "",
                  "| Figure | Code | Decoder | p | Published | Local estimate | Local 95% interval | Approx. source 95% interval | Overlap? |",
                  "|---:|---|---|---:|---:|---:|---:|---:|---|"])
    for row in exclusions:
        label = (f'IS {row["local_rate"]:.6g}, ESS={row["importance_failure_ess"]:.1f}'
                 if row["estimator"] == "mixture_importance" else f'{row["failures"]}/{row["shots"]} ({row["local_rate"]:.6g})')
        lines.append(f'| {row["figure"]} | {row["code"].upper()} | {row["curve"]} | {float(row["p"]):.2f} | {row["published_rate"]:.6g} | {label} | [{row["ci95_low"]:.6g}, {row["ci95_high"]:.6g}] | [{row["source_approx_ci95_low"]:.6g}, {row["source_approx_ci95_high"]:.6g}] | {row["source_mc_compatibility"]} |')
    lines.extend(["", "At B1 T=1, p=0.06, the local 100/12,358 estimate excludes the plotted 0.00606 point. Figure 3 says its points were also collected to 100 failures; approximating that source run as 100/16,502 gives a 95% interval that overlaps the local interval. This is a reproducibility lead, not evidence of a specific kernel error."])
    lines.extend(["", "## Table 1: decimated variables", "",
                  "The paper specifies different T values in its prose and caption. The executed T=10 mean is shown separately.", "",
                  "| p | Source mean | Source shots | Local T=10 mean ± SE | Local shots |", "|---:|---:|---:|---:|---:|"])
    for p, mean, source_shots in zip(SOURCE["table_1"]["p"], SOURCE["table_1"]["mean"], SOURCE["table_1"]["shots"]):
        item = runs.get(("b1", "bpgd_t10", f"{p:.5f}"))
        local_mean = "—" if item is None else f'{item["counts"]["fixations"] / item["shots"]:.3f} ± {item["fixations_se"]:.3f}'
        local_shots = "—" if item is None else str(item["shots"])
        lines.append(f"| {p:.2f} | {mean:.2f} | {source_shots:,} | {local_mean} | {local_shots} |")
    b1_p008 = runs.get(("b1", "bpgd_t10", "0.08000"))
    if b1_p008 is not None:
        lines.extend(["", f'At B1 p=0.08, {b1_p008["counts"]["type_i"]} of {b1_p008["failures"]} local guided failures are syndrome-inconsistent (Type I), while {b1_p008["counts"]["type_ii"]} are logical (Type II). This is consistent with the paper\'s statement that over 90% of these failures are non-convergence cases.'])
    c2_p007 = runs.get(("c2", "bpgd_t10", "0.07000"))
    if c2_p007 is not None:
        provenance = ("a recovered prefix" if c2_p007.get("evidence_tier") == "interrupted_prefix"
                      else "a completed direct run")
        lines.extend(["", f'C2 p=0.07 used {provenance} of {c2_p007["shots"]} shots: '
                      f'{c2_p007["counts"]["type_i"]} Type I and '
                      f'{c2_p007["counts"]["type_ii"]} Type II failures.'])
    lines.extend(["", "## Table 2: fixed-error randomized decimation", "",
                  "The published 9,568/10,000 convergences and 111 distinct convergent corrections depend on fixed error bytes that were not released. The paper uses T=10, p=0.08, and top-gap randomization with gap 1.0. The following runs use newly seeded weight-73 errors and are not direct numerical comparisons.", "",
                  "| Local surrogate | Error selection | Trials | Converged | Distinct valid corrections | Distinct all candidates | Type I | Type II |", "|---|---|---:|---:|---:|---:|---:|---:|"])
    for path in sorted((result).glob("table2-*/summary.json")):
        item = json.loads(path.read_text())
        manifest = path.with_name("manifest.json")
        ledger = path.with_name("events.jsonl")
        recorded = json.loads(manifest.read_text())
        if recorded.get("source_sha256") != sha256((ROOT / "table2_surrogate.py").read_bytes()).hexdigest():
            continue  # Retain historical pilots but do not present unreplayable code revisions.
        if (sha256(manifest.read_bytes()).hexdigest() != item["manifest_sha256"]
                or sha256(ledger.read_bytes()).hexdigest() != item["events_sha256"]):
            raise ValueError(f"Table 2 surrogate hash mismatch: {path}")
        selection = recorded["error_selection"]
        distinct_all = len({json.loads(row)["candidate_sha256"] for row in ledger.read_text().splitlines()})
        lines.append(f'| {path.parent.name} | {selection} | {item["trials"]} | {item["counts"]["converged"]} | {item["distinct_converged_corrections"]} | {distinct_all} | {item["counts"]["type_i"]} | {item["counts"]["type_ii"]} |')
    lines.extend(["", "## Source and scope notes", "",
                  "- Coverage counts plotted figure coordinates; identical BP rates repeated in several figures count more than once.",
                  "- Figures 3 and 4 publish different values for the nominally identical B1 T=10 curve. Both are retained as separate targets.",
                  "- Table 1's prose says T=10; its caption says T=100. The local fixations are reported under the actual executed T.",
                  "- Table 2's fixed error bytes were not published; its exact 10,000-run result cannot be reproduced from the source artifact.",
                  "- A superseded Table 2 smoke run remains on disk but is omitted from the table because its historical script bytes were not retained. The two displayed surrogates bind the current script hash.",
                  "- The comparison omits BP-OSD and BP-SI. The pinned raw source extraction retains their provenance, but neither appears in this BP/BPGD table or plot.",
                  "- Plain QBP v2 counts are imported from the earlier vanilla campaign, not rerun here. Its archive hash matches this source, but its recorded main.tex hash has a transcription error; this study records the independently verified TeX hash. The earlier count ledgers were not revalidated by this assessor.",
                  "- The new binary path is a compiled interpretation of the paper's V2C clipping and decimation pseudocode. The A5/B2 Q-BPGD path uses the existing compiled BP4 v2 kernel; these are canonical adaptations.",
                  "- Q-BPGD follows Algorithm 3's T-sweep, syndrome-test, maximum-marginal decimation order. Its local V2C state persists between rounds. The paper does not specify its Q-BP numerical safeguards or message restart behavior, so a separated curve point cannot yet be attributed to either policy.",
                  "- All local results include Type I and Type II block failures. A correction differing from the sampled error by a stabilizer counts as success.",
                  "- Reaching 100 direct failures at the source B1 T=100, p=0.04 rate of 10⁻⁶ requires about 100 million shots in expectation; B1 T=10 at p=0.04 requires about 16.7 million. Rare-event estimates are explicitly marked IS and require the precision gate above before they are considered resolved.",
                  "", "The complete point table is [comparison.csv](comparison.csv); plots are [comparison.png](comparison.png) and [comparison.pdf](comparison.pdf).", ""])
    (result / "REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    write_outputs()
