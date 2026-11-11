"""Read-only catalog adapters for retained research evidence.

This module deliberately normalizes *summary* files.  It does not interpret a
missing ledger as a zero-result, start a campaign, or copy HPC-only raw data
into an export.  The source registry under ``research/catalog`` is the small,
reviewable index of the real retained sources.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any


_POINT_KEYS = (
    "x", "y", "n", "failures", "ci_low", "ci_high", "status", "mean_work",
    "work_unit", "mean_seconds", "type_i", "type_ii", "source_value",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(repository: Path, path: Path) -> str:
    return path.relative_to(repository).as_posix()


@lru_cache(maxsize=8)
def _tracked_paths(repository_text: str) -> frozenset[str]:
    """Use Git's index, never file existence, for portable-download claims."""
    result = subprocess.run(("git", "-C", repository_text, "ls-files", "-z"), check=True,
                            capture_output=True)
    return frozenset(item.decode("utf-8") for item in result.stdout.split(b"\0") if item)


def _asset(repository: Path, relative_path: str, *, label: str, kind: str,
           availability: str | None = None) -> dict[str, Any]:
    path = repository / relative_path
    tracked = relative_path in _tracked_paths(str(repository))
    local_only = availability == "local_only" or (path.exists() and not tracked)
    actual_availability = "local_only" if local_only else "tracked" if tracked else "unavailable"
    return {
        "label": label,
        "path": relative_path,
        "url": relative_path if actual_availability == "tracked" else None,
        "kind": kind,
        "availability": actual_availability,
        "local_storage_path": relative_path if actual_availability == "local_only" else None,
        "sha256": sha256(path.read_bytes()).hexdigest() if path.exists() and path.is_file() else None,
    }


def _number(value: str | None) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    return float(value)


def _integer(value: str | None) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _point(**values: Any) -> dict[str, Any]:
    point = {key: values.get(key) for key in _POINT_KEYS}
    if "metadata" in values:
        point["metadata"] = values["metadata"]
    return point


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _dataset(dataset_id: str, *, label: str, paper_id: str, evidence_status: str,
             source_path: str, points: list[dict[str, Any]], assets: list[dict[str, Any]],
             caveat: str) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "label": label,
        "paper_id": paper_id,
        "evidence_status": evidence_status,
        "source_path": source_path,
        "points": points,
        "assets": assets,
        "caveat": caveat,
    }


def _presentation_datasets(repository: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = "from_dr_pfister_presentetations/results"
    source_path = f"{root}/source_curves.csv"
    source_points = [
        _point(x=_number(row["p"]), y=_number(row["reported_ler"]),
               n=_integer(row["reported_trials"]),
               # The source marks this one point as a zero-failure one-sided
               # upper bound.  It is not an observed rate, but its supplied
               # denominator and zero count remain useful source metadata.
               failures=(0 if row["point_type"] == "upper_95_one_sided" and _integer(row["reported_trials"]) is not None else None),
               status="source_transcription",
               source_value=_number(row["reported_ler"]),
               metadata={"source_point_type": row["point_type"], "is_rate_estimate": row["point_type"] == "observed",
                         "uncertainty_method": ("exact_one_sided_95_percent_upper_bound"
                                                if row["point_type"] == "upper_95_one_sided" else "source_not_supplied"),
                         "confidence_level": 0.95 if row["point_type"] == "upper_95_one_sided" else None,
                         "denominator_definition": ("source-reported trial count; zero observed failures underpin the one-sided bound"
                                                    if _integer(row["reported_trials"]) is not None else "source denominator unavailable"),
                         "reported_trials_basis": ("source_reported" if _integer(row["reported_trials"]) is not None else "unavailable")})
        for row in _csv_rows(repository / source_path)
    ]
    source = _dataset(
        "pfister-presentation-source-curves", label="Presentation source-curve transcription",
        paper_id="pfister-presentation-excerpt", evidence_status="source_transcription",
        source_path=source_path, points=source_points,
        assets=[_asset(repository, source_path, label="Transcribed source curves", kind="csv"),
                _asset(repository, f"{root}/source_claims.csv", label="Recorded slide claims", kind="csv")],
        caveat="Presentation TeX and per-shot data were not supplied; denominators are generally unknown.",
    )
    pilot_path = f"{root}/pilot_summary.csv"
    pilot_points = [
        _point(x=_number(row["p"]), y=_number(row["local_ler"]), n=_integer(row["local_trials"]),
               failures=_integer(row["local_failures"]), ci_low=_number(row["local_95_exact_two_sided_low"]),
               ci_high=_number(row["local_95_exact_two_sided_high"]), status="pilot_adaptation",
               mean_work=_number(row["mean_bp4_equivalent_work"]), work_unit="BP4-equivalent iterations",
               type_i=_integer(row["invalid_syndrome"]), source_value=_number(row["reported_ler_or_upper"]))
        for row in _csv_rows(repository / pilot_path)
    ]
    pilot = _dataset(
        "pfister-presentation-local-pilots", label="Presentation local paired pilots",
        paper_id="pfister-presentation-excerpt", evidence_status="canonical_adaptation",
        source_path=pilot_path, points=pilot_points,
        assets=[_asset(repository, pilot_path, label="Pilot summary", kind="csv"),
                _asset(repository, f"{root}/pilot_paired_summary.csv", label="Paired pilot summary", kind="csv"),
                _asset(repository, f"{root}/pilot_b1_p0.100_n100_seed20261025_t1000.events.jsonl",
                       label="Example raw ledger", kind="jsonl")],
        caveat="Local policy choices resolve slide omissions; these pilots are not source-faithful reproductions.",
    )
    return [source, pilot], []


def _vanilla_dataset(repository: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = "data/reproductions/yao-2312-10950-vanilla/results/comparison.csv"
    points = [
        _point(x=_number(row["p"]), y=_number(row["rate"]), n=_integer(row["shots"]),
               failures=_integer(row["failures"]), ci_low=_number(row["ci95_low"]), ci_high=_number(row["ci95_high"]),
               status="complete" if row["complete"] == "True" else "incomplete",
               mean_work=_number(row["mean_bp4_equivalent_iterations"]), work_unit="BP4-equivalent iterations",
               mean_seconds=(_number(row["mean_decode_ms"]) or 0.0) / 1000,
               type_i=_integer(row["type_i"]), type_ii=_integer(row["type_ii"]),
               source_value=_number(row["source_qbp_rate"]))
        for row in _csv_rows(repository / path)
    ]
    dataset = _dataset(
        "yao-vanilla-a5-b2", label="Yao A5/B2 vanilla BP comparison", paper_id="yao-2312-10950-v2",
        evidence_status="canonical_adaptation", source_path=path, points=points,
        assets=[_asset(repository, path, label="Comparison table", kind="csv"),
                _asset(repository, "data/reproductions/yao-2312-10950-vanilla/results/merged.json", label="Merged receipt", kind="json"),
                _asset(repository, "data/reproductions/yao-2312-10950-vanilla/source_points.json", label="Pinned source points", kind="json"),
                _asset(repository, "data/reproductions/yao-2312-10950-vanilla/results/shards/a5_p04_0120000/events.jsonl.zst",
                       label="Per-shot raw ledger (compressed)", kind="jsonl_zstd")],
        caveat="Source denominators and full Q-BP numerical conventions are unavailable; source interval containment is descriptive only.",
    )
    decoders = []
    for filename in ("bp4_v1.json", "bp4_v2.json", "binary_v1.json", "binary_v2.json"):
        relative = f"data/reproductions/yao-2312-10950-vanilla/decoders/{filename}"
        decoders.append({"decoder_id": f"yao-vanilla-{filename[:-5]}", "label": filename[:-5],
                         "evidence_status": "canonical_adaptation", "asset": _asset(repository, relative, label=filename, kind="decoder_policy"),
                         "configuration": _read_json(repository / relative)})
    return dataset, decoders


def _tuning_dataset(repository: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = "data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/evaluation_results.csv"
    points = [
        _point(x=0.06, y=_number(row["ler"]), n=_integer(row["shots"]), failures=_integer(row["failures"]),
               ci_low=_number(row["ci90_lower"]), ci_high=_number(row["ci90_upper"]), status="complete",
               mean_work=_number(row["mean_iterations"]), work_unit="BP4 iterations",
               mean_seconds=(_number(row["mean_decode_ms"]) or 0.0) / 1000,
               type_i=_integer(row["type_i"]), type_ii=_integer(row["type_ii"]),
               metadata={"confidence_level": 0.90, "uncertainty_method": "two_sided_exact_binomial_interval",
                         "denominator_definition": "fixed matched-shot cohort"})
        for row in _csv_rows(repository / path)
    ]
    dataset = _dataset(
        "yao-bp4-tuning-fairness-p006", label="A5/B2 tuned BP4 fairness follow-up", paper_id="yao-2312-10950-v2",
        evidence_status="controlled_canonical_adaptation", source_path=path, points=points,
        assets=[_asset(repository, path, label="Fairness evaluation", kind="csv"),
                _asset(repository, "data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/evaluation_results.json", label="Paired comparisons", kind="json")],
        caveat="Use this equal-cap/equal-mean-work follow-up for tuning effects; long-cap selection rates are not a fair work comparison.",
    )
    decoders = []
    for code in ("a5", "b2"):
        relative = f"data/reproductions/yao-2312-10950-bp4-tuning-p006/decoders/{code}_tuned.json"
        decoders.append({"decoder_id": f"yao-tuned-bp4-{code}", "label": f"Tuned BP4 {code.upper()}",
                         "evidence_status": "canonical_tuning", "asset": _asset(repository, relative, label=f"{code} selected policy", kind="decoder_policy"),
                         "configuration": _read_json(repository / relative)})
    return dataset, decoders


def _cross_code_dataset(repository: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = "data/reproductions/yao-2312-10950-cross-code/results/performance.csv"
    points = [
        _point(x=_number(row["p"]), y=_number(row["rate"]), n=_integer(row["shots"]), failures=_integer(row["failures"]),
               ci_low=_number(row["ci95_low"]), ci_high=_number(row["ci95_high"]), status="complete",
               mean_work=_number(row["mean_directed_edge_updates"]), work_unit="directed edge updates",
               mean_seconds=(_number(row["mean_decode_ms"]) or 0.0) / 1000,
               type_i=_integer(row["type_i"]), type_ii=_integer(row["type_ii"]),
               metadata={"channel": row["channel"], "maximum_iterations": _integer(row["T"]),
                         "source_evidence_path": row["evidence"],
                         "uncertainty_method": "two_sided_95_percent_binomial_interval",
                         "denominator_definition": "all terminal shots in the retained result row"})
        for row in _csv_rows(repository / path)
    ]
    return _dataset(
        "yao-cross-code-plain-baselines", label="Yao missing plain-decoder baselines", paper_id="yao-2312-10950-v2",
        evidence_status="controlled_local_baseline", source_path=path, points=points,
        assets=[_asset(repository, path, label="Performance table", kind="csv"),
                _asset(repository, "data/reproductions/yao-2312-10950-cross-code/results/paired.csv", label="Paired effects", kind="csv"),
                _asset(repository, "data/reproductions/yao-2312-10950-cross-code/decoders.json", label="Frozen policies", kind="decoder_policy")],
        caveat="The paper has no point for these missing code-decoder arms; cross-channel code quality is not inferred.",
    ), {"decoder_id": "yao-cross-code-plain-policies", "label": "Cross-code plain BP policies",
          "evidence_status": "controlled_local_baseline",
          "asset": _asset(repository, "data/reproductions/yao-2312-10950-cross-code/decoders.json", label="Frozen policies", kind="decoder_policy"),
          "configuration": _read_json(repository / "data/reproductions/yao-2312-10950-cross-code/decoders.json")}


_YAO_COMPLETION = "data/reproductions/yao-2312-10950-bpgd-completion"
_YAO_COMPLETION_DATASET = "yao-bpgd-completion"


def _yao_completion_dataset(repository: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    plan_path = f"{_YAO_COMPLETION}/plan.json"
    plan_file = repository / plan_path
    paths = [f"{_YAO_COMPLETION}/verified.json", f"{_YAO_COMPLETION}/results/verified.json"]
    candidates = [(path, _read_json(repository / path)) for path in paths if (repository / path).exists()]
    if not candidates:
        return {}, [], {}
    plan_digest = sha256(plan_file.read_bytes()).hexdigest()
    for _, candidate in candidates:
        if (candidate["schema"] != "yao-bpgd-completion-verification-v1"
                or candidate["plan_sha256"] != plan_digest):
            raise ValueError("Yao completion verification does not match the frozen plan")
    # Prefer the portable snapshot on ties. The HPC collector may have verified
    # additional points after the latest snapshot was committed.
    path, receipt = max(candidates, key=lambda item: len(item[1]["points"]))
    plan = _read_json(plan_file)
    rows = receipt["points"]
    points = []
    for row in rows:
        n, failures = row["shots"], row["failures"]
        settings = plan["arms"][f'{row["code"]}:{row["arm"]}']
        counts = row["counts"]
        p = row["physical_p"]
        points.append(_point(
            x=p, y=row["rate"], n=n, failures=failures,
            ci_low=row["ci95_low"], ci_high=row["ci95_high"],
            status="upper_bound" if failures == 0 else "complete",
            type_i=counts["type_i"], type_ii=counts["type_ii"],
            mean_work=row["iterations"] / n, work_unit="iterations",
            mean_seconds=row["decode_ns"] / n / 1e9,
            metadata={
                "channel": settings["noise_model"], "matched_x_rate": row["matched_x_rate"],
                "sampling_method": "iid_failure_target_or_shot_cap",
                "stop_reason": row["stop_reason"],
                "target_failures": plan["stop"]["target_block_failures"],
                "max_shots": plan["stop"]["max_shots"],
                "seed": plan["seed"], "source_targets": row["source_targets"],
                "source_evidence_path": f'{_YAO_COMPLETION}/results/{row["id"]}/summary.json',
                "summary_sha256": row["summary_sha256"], "ledger_sha256": row["ledger_sha256"],
                "uncertainty_method": ("exact_negative_binomial_interval"
                                       if row["stop_reason"] == "target_block_failures"
                                       else "exact_binomial_interval_at_shot_cap"),
                "denominator_definition": "all retained iid shots; syndrome mismatch or nontrivial logical residual",
            },
        ))
    dataset = _dataset(
        _YAO_COMPLETION_DATASET, label="B1/C2 direct BPGD and matched-marginal Q-BP",
        paper_id="yao-2312-10950-v2", evidence_status="source_informed_canonical_adaptation",
        source_path=path, points=points,
        assets=[_asset(repository, plan_path, label="Frozen decoder settings and campaign", kind="json"),
                _asset(repository, path, label="Verified terminal results", kind="json")],
        caveat="BPGD uses X-only noise. Q-BP uses joint depolarizing noise at 1.5 times the bit-flip rate. "
               "The X marginals match and the underlying channels differ. Sweep caps specify iterations per shot.",
    )
    return dataset, rows, plan["arms"]


def _non_osd_dataset(repository: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = "data/reproductions/yao-2312-10950-non-osd/results/comparison.csv"
    rows = _csv_rows(repository / path)
    points = []
    for row in rows:
        is_importance = row["estimator"] == "mixture_importance"
        points.append(_point(
            x=_number(row["p"]), y=_number(row["local_rate"]),
            # A weighted importance estimate is not failures / raw samples.
            n=None if is_importance else _integer(row["shots"]),
            failures=None if is_importance else _integer(row["failures"]),
            ci_low=_number(row["ci95_low"]), ci_high=_number(row["ci95_high"]), status=row["assessment"],
            mean_work=_number(row["mean_iterations"]), work_unit="iterations",
            mean_seconds=(None if _number(row["mean_decode_ms"]) is None else _number(row["mean_decode_ms"]) / 1000),
            type_i=None if is_importance else _integer(row["type_i"]),
            type_ii=None if is_importance else _integer(row["type_ii"]), source_value=_number(row["published_rate"]),
            metadata={
                "estimator": row["estimator"], "sampling_method": row["evidence_tier"],
                "uncertainty_method": "weighted_importance_interval" if is_importance else "two_sided_95_percent_binomial_interval",
                "denominator_definition": "weighted target/mixture likelihood mass" if is_importance else "all sampled iid shots",
                "raw_samples": _integer(row["shots"]), "raw_failures": _integer(row["failures"]),
                "raw_type_i": _integer(row["type_i"]), "raw_type_ii": _integer(row["type_ii"]),
                "weighted_estimate": _number(row["importance_rate"]) if is_importance else None,
                "weighted_ci_low": _number(row["importance_ci95_low"]) if is_importance else None,
                "weighted_ci_high": _number(row["importance_ci95_high"]) if is_importance else None,
                "weighted_failure_effective_n": _number(row["importance_failure_ess"]) if is_importance else None,
                "importance_stage": _integer(row["importance_stage"]) if is_importance else None,
                "importance_stage_complete": row["importance_stage_complete"] if is_importance else None,
                # The same retained local measurement can be compared to
                # several source figures.  Retain that figure scope instead
                # of silently plotting the same local point repeatedly in a
                # single series with conflicting source comparisons.
                "source_figure": row["figure"],
                "source_evidence_path": row["evidence_path"],
                "source_assessment": row["assessment"],
                "source_assessment_reason": row["assessment_reason"],
            },
        ))
    return _dataset(
        "yao-non-osd-results", label="Yao BP/BPGD non-OSD results", paper_id="yao-2312-10950-v2",
        evidence_status="source_informed_canonical_adaptation", source_path=path, points=points,
        assets=[_asset(repository, path, label="Comparison table", kind="csv"),
                _asset(repository, "data/reproductions/yao-2312-10950-non-osd/source_points.json", label="Pinned TeX extraction", kind="json"),
                _asset(repository, "data/reproductions/yao-2312-10950-non-osd/codes.json", label="Code receipts", kind="json")],
        caveat="Rows retain iid and mixture-importance estimators separately; source-figure comparisons and paper numerical safeguards remain distinct.",
    ), rows


def _qbpgd_datasets(repository: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep the exploratory and confirmation Q-BPGD cohorts disjoint.

    Both retained cohorts use p=0.06 and the same arms, so grouping solely by
    code and arm makes them look like two measurements of one curve.  They are
    distinct runs with distinct seeds and planned shot counts, and must remain
    separately selectable evidence records.
    """
    root_relative = "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/results"
    root = repository / root_relative
    cohort_specs = {
        10000: {
            "dataset_id": "yao-tuned-qbpgd-p006",
            "label": "Tuned BP4 within Q-BPGD confirmation",
            "cohort_kind": "confirmation",
            "caveat": "The 10,000-shot confirmation cohort uses selected local BP4 profiles, not unpublished author settings. It is not pooled with the 1,000-shot pilot.",
        },
        1000: {
            "dataset_id": "yao-tuned-qbpgd-p006-pilot-n1000",
            "label": "Tuned BP4 within Q-BPGD pilot (1,000 shots)",
            "cohort_kind": "pilot",
            "caveat": "Exploratory 1,000-shot pilot retained for provenance only. It is distinct from and must not be pooled or plotted as the 10,000-shot confirmation cohort.",
        },
    }
    cohorts: dict[int, dict[str, Any]] = {
        shots: {"points": [], "assets": [], "series": [], "summaries": []}
        for shots in cohort_specs
    }
    for summary_path in sorted(root.glob("*/summary.json")):
        summary = _read_json(summary_path)
        shots = int(summary["shots"])
        if shots not in cohort_specs:
            raise ValueError(f"unrecognized Q-BPGD cohort size {shots} in {summary_path}")
        specification = cohort_specs[shots]
        relative_summary = _relative(repository, summary_path)
        cohort = cohorts[shots]
        cohort["assets"].append(_asset(repository, relative_summary, label=f"{summary_path.parent.name} summary", kind="json"))
        cohort["summaries"].append({"code": summary["code"], "seed": summary["seed"], "shots": shots,
                                    "summary_path": relative_summary, "events_sha256": summary["events_sha256"],
                                    "manifest_sha256": summary["manifest_sha256"]})
        for arm, values in summary["counts"].items():
            failures = int(values["type_i"]) + int(values["type_ii"])
            point = _point(
                x=0.06, y=failures / shots, n=shots, failures=failures, status="complete",
                mean_work=values["iterations"] / shots, work_unit="BP4 sweeps",
                mean_seconds=values["elapsed_ns"] / shots / 1e9,
                type_i=values["type_i"], type_ii=values["type_ii"],
                metadata={"cohort_kind": specification["cohort_kind"], "summary_path": relative_summary,
                          "seed": summary["seed"], "events_sha256": summary["events_sha256"],
                          "manifest_sha256": summary["manifest_sha256"],
                          "denominator_definition": "all terminal shots in this retained cohort",
                          "uncertainty_method": "source_summary_has_no_interval"},
            )
            cohort["points"].append(point)
            cohort["series"].append({
                "dataset_id": specification["dataset_id"], "code_id": summary["code"], "decoder_id": arm,
                "label": f"{specification['label']}: {summary['code']} / {arm}", "points": [point],
                "cohort_kind": specification["cohort_kind"], "summary_path": relative_summary,
            })

    datasets: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    for shots in (10000, 1000):
        specification = cohort_specs[shots]
        cohort = cohorts[shots]
        if not cohort["summaries"]:
            raise ValueError(f"missing retained Q-BPGD {specification['cohort_kind']} cohort")
        dataset = _dataset(
            specification["dataset_id"], label=specification["label"], paper_id="yao-2312-10950-v2",
            evidence_status="canonical_adaptation", source_path=root_relative,
            points=cohort["points"], assets=cohort["assets"], caveat=specification["caveat"],
        )
        dataset["cohort"] = {"kind": specification["cohort_kind"], "shots_per_arm": shots,
                             "retained_summaries": sorted(cohort["summaries"], key=lambda item: item["code"])}
        datasets.append(dataset)
        series.extend(cohort["series"])
    return datasets, series


def _bb72_datasets(repository: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Adapt the three completed BB72 summaries without exposing their ledgers."""
    fair_path = "data/results/fair-beam-relay-css-v2/result.json"
    fair = _read_json(repository / fair_path)
    fair_points: list[dict[str, Any]] = []
    fair_rows: list[tuple[str, str]] = []
    for rate, gammas in fair["selected_summaries"].items():
        for gamma, methods in gammas.items():
            for method, row in methods.items():
                fair_points.append(_point(x=int(rate[1:]) / 1000, y=row["failures"] / row["shots"], n=row["shots"],
                                          failures=row["failures"], ci_low=row["failure_interval_95"][0], ci_high=row["failure_interval_95"][1],
                                          status=fair["assessment_status"], mean_work=row["mean_total_c2v"], work_unit="C2V updates",
                                          mean_seconds=row["mean_runtime_ms"] / 1000,
                                          metadata={"selected_profile": row["selected_profile"], "damping_gamma": gamma,
                                                    "selection_status": "frozen_before_evaluation",
                                                    "uncertainty_method": "two_sided_95_percent_binomial_interval",
                                                    "denominator_definition": "all terminal matched evaluation shots",
                                                    "raw_asset": _asset(repository, f"data/results/fair-beam-relay-css-v2/evaluation/{rate}/{row['selected_profile']}/events.jsonl.gz", label=f"{rate} {row['selected_profile']} matched raw ledger", kind="jsonl_gz")}))
                # Profile selection is rate/damping/method specific; retaining
                # it in the ID prevents a p050 i10 arm and p080 i05 arm from
                # appearing to be one decoder configuration.
                fair_rows.append(("BB72", f"{method}-{gamma}-{row['selected_profile']}"))
    fair_dataset = _dataset("bb72-fair-beam-relay-v2", label="BB72 selected BeamSearch/RelayBP settings",
                            paper_id="relaybp-2506-01779-v2", evidence_status="controlled_css_adaptation", source_path=fair_path,
                            points=fair_points,
                            assets=[_asset(repository, fair_path, label="Verified result", kind="json"),
                                    _asset(repository, "data/results/fair-beam-relay-css-v2/publication-manifest.json", label="Publication manifest", kind="json"),
                                    _asset(repository, "data/results/fair-beam-relay-css-v2/evaluation/p050/i05/events.jsonl.gz", label="Representative raw evaluation ledger", kind="jsonl_gz")],
                            caveat=fair["claim_limit"])
    fair_dataset["paper_ids"] = ["relaybp-2506-01779-v2", "beamsearch-2512-07057-v2"]
    bpsf_path = "data/results/bb72-bpsf-factorial-v2/result.json"
    bpsf = _read_json(repository / bpsf_path)
    bpsf_points: list[dict[str, Any]] = []
    bpsf_rows: list[tuple[str, str]] = []
    for rate, rows in bpsf["summaries"].items():
        for configuration, row in rows.items():
            runtime = row.get("runtime", {})
            work = row.get("mean_work_vector", {}).get("check_to_variable_updates")
            bpsf_points.append(_point(x=int(rate[1:]) / 1000, y=row["failure_rate"], n=row["shots"], failures=row["failures"],
                                      ci_low=row["failure_interval_95"][0], ci_high=row["failure_interval_95"][1], status="complete",
                                      mean_work=work, work_unit="C2V updates", mean_seconds=(runtime["mean_ns"] / 1e9 if runtime.get("mean_ns") is not None else None),
                                      metadata={"uncertainty_method": "two_sided_95_percent_binomial_interval", "denominator_definition": "all terminal matched evaluation shots",
                                                "runtime_scope": runtime.get("scope"), "runtime_method": runtime.get("method"),
                                                "runtime_available_shots": runtime.get("available_shots"),
                                                "runtime_comparison_status": "not_comparable_across_controller_and_decode_scopes",
                                                "raw_asset": _asset(repository, f"data/results/bb72-bpsf-factorial-v2/{rate}/{configuration}/events.jsonl.gz", label=f"{rate} {configuration} raw ledger", kind="jsonl_gz")}))
            bpsf_rows.append(("BB72", configuration))
    bpsf_dataset = _dataset("bb72-bpsf-factorial-v2", label="BB72 BP-SF factorial study", paper_id="bpsf-2507-00254-v1",
                            evidence_status="controlled_css_adaptation", source_path=bpsf_path, points=bpsf_points,
                            assets=[_asset(repository, bpsf_path, label="Verified factorial result", kind="json"),
                                    _asset(repository, "data/studies/bb72-bpsf-factorial-v2.json", label="Frozen study design", kind="study_design")],
                            caveat=bpsf["claim_limit"])
    datasets = [fair_dataset, bpsf_dataset]
    grouped_series: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for dataset, rows in ((fair_dataset, fair_rows), (bpsf_dataset, bpsf_rows)):
        for point, (code_id, decoder_id) in zip(dataset["points"], rows, strict=True):
            grouped_series.setdefault((dataset["dataset_id"], code_id, decoder_id), []).append(point)
    series = [
        {"dataset_id": dataset_id, "code_id": code_id, "decoder_id": decoder_id,
         "label": f"{next(dataset['label'] for dataset in datasets if dataset['dataset_id'] == dataset_id)}: {decoder_id}",
         "points": sorted(points, key=lambda point: point["x"])}
        for (dataset_id, code_id, decoder_id), points in sorted(grouped_series.items())
    ]
    decoders = []
    for decoder_id in sorted({series_item["decoder_id"] for series_item in series}):
        study_path = "data/studies/fair-beam-relay-css-v2.json" if decoder_id.startswith(("beam", "relay")) else "data/studies/bb72-bpsf-factorial-v2.json"
        decoders.append({"decoder_id": decoder_id, "label": f"BB72 {decoder_id}", "evidence_status": "controlled_css_adaptation",
                         "asset": _asset(repository, study_path, label="Frozen BB72 configuration", kind="study_design"),
                         "configuration": {"source_path": study_path, "configuration_id": decoder_id}})
    return datasets, series, decoders


def _local_curve_dataset(repository: Path, *, dataset_id: str, label: str, path: str,
                         decoder_field: str, rate_field: str, failures_field: str,
                         shots_field: str, lower_field: str, upper_field: str,
                         work_field: str, status: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = _csv_rows(repository / path)
    points = [_point(x=_number(row["p"]), y=_number(row[rate_field]), n=_integer(row[shots_field]),
                     failures=_integer(row[failures_field]), ci_low=_number(row[lower_field]), ci_high=_number(row[upper_field]),
                     status=status, mean_work=_number(row[work_field]), work_unit="BP4 iterations",
                     mean_seconds=_number(row.get("mean_elapsed_seconds")), type_i=_integer(row.get("type_i")),
                     type_ii=_integer(row.get("type_ii")), source_value=_number(row.get("source_rate_or_bound") or row.get("source_ler")),
                     metadata={"source_point_type": row.get("source_point_type", "observed"),
                               "source_value_is_bound": row.get("source_point_type") == "upper_95_one_sided",
                               "uncertainty_method": "two_sided_95_percent_binomial_interval",
                               "denominator_definition": "local fixed-shot denominator"})
              for row in rows]
    return _dataset(dataset_id, label=label, paper_id="pfister-presentation-excerpt", evidence_status="canonical_adaptation",
                    source_path=path, points=points,
                    assets=[_asset(repository, path, label="Curve comparison", kind="csv"),
                            _asset(repository, str(Path(path).parent / "analysis.json"), label="Analysis receipt", kind="json")],
                    caveat="Local float64/corrected numerical-policy evidence; it remains distinct from the supplied presentation transcription."), rows


def _study_records(repository: Path, source_registry: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for relative in source_registry["study_paths"]:
        path = repository / relative
        if not path.exists():
            continue
        value = _read_json(path)
        records.append({"study_id": value.get("study_id", path.stem), "label": value.get("question", value.get("study_id", path.stem)),
                        "status": value.get("assessment_status", value.get("status", value.get("claim_status", "recorded"))),
                        "source_status": value.get("source_status", value.get("claim_scope", "local_study")),
                        "asset": _asset(repository, relative, label=path.name, kind="study_design"), "configuration": value})
    return records


def _grouped_series(dataset_id: str, points: list[dict[str, Any]], rows: list[dict[str, str]], *,
                    code_field: str, decoder_field: str, label_prefix: str,
                    scope_field: str | None = None) -> list[dict[str, Any]]:
    """Keep UI series tied to the same ordered rows used for a dataset."""
    grouped: dict[tuple[str, str, str | None], list[dict[str, Any]]] = {}
    for point, row in zip(points, rows, strict=True):
        scope = row[scope_field] if scope_field is not None else None
        key = (row[code_field], row[decoder_field], scope)
        grouped.setdefault(key, []).append(point)
    return [
        {"dataset_id": dataset_id, "code_id": code, "decoder_id": decoder,
         "label": f"{label_prefix}: {code} / {decoder}" + (f" / {scope_field} {scope}" if scope is not None else ""),
         "points": grouped[(code, decoder, scope)],
         **({"series_scope": {scope_field: scope}, "decoder_identity_scope": f"{scope_field}-{scope}"}
            if scope is not None and scope_field is not None else {})}
        for code, decoder, scope in sorted(grouped)
    ]


def _fallback_recipe(dataset_id: str, source_path: str) -> dict[str, Any]:
    """Return only documented inspection or bounded-extension commands.

    These records deliberately do not turn an immutable completed cohort into
    a browser-run campaign. Compute-bearing commands name the retained CLI
    and require a fresh study/output identity where the documentation says it
    is necessary.
    """
    source_only = {
        "kind": "retained_source_only", "study_path": source_path, "decoder_path": None,
        "commands": [], "original_instruction_path": "from_dr_pfister_presentetations/README.md",
        "budget_note": "This is a supplied curve transcription, not a repository simulation. The source raw data and simulator were not supplied.",
    }
    recipes: dict[str, dict[str, Any]] = {
        "pfister-presentation-source-curves": source_only,
        "pfister-presentation-local-pilots": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/verify_spike.py",
                ".venv/bin/python from_dr_pfister_presentetations/plot_results.py",
            ],
            "bounded_extension_commands": [
                "PYTHONPATH=src .venv/bin/python from_dr_pfister_presentetations/run_reproduction.py --code double_gross --p 0.08 --shots 100 --seed 20261110",
            ],
            "original_instruction_path": "from_dr_pfister_presentetations/README.md",
            "budget_note": "The retained pilot cohorts are immutable. The extension command is a new 100-shot adaptation pilot (fresh seed), not a regeneration or pooling of the recorded cohort.",
        },
        "pfister-presentation-full-v2-curves": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/analyze_full_v2_curves.py",
            ],
            "bounded_extension_commands": [
                "PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/run_full_v2_curve.py --code b1 --p 0.12 --seed 20261110 --output /path/to/new/b1-p012 --max-iterations 1000 --target-failures 30 --max-shots 20000",
            ],
            "original_instruction_path": "from_dr_pfister_presentetations/results/full_v2_curves/README.md",
            "budget_note": "The analyzer verifies retained ledger hashes. The extension is an independently bounded 20,000-shot output directory and is not part of the frozen full-v2 curve.",
        },
        "pfister-presentation-ms-both-changes": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/analyze_ms_both_changes_curve.py",
            ],
            "original_instruction_path": "from_dr_pfister_presentetations/results/ms_both_changes_curve/README.md",
            "budget_note": "This retained nine-point Q8 diagnostic and its independent holdout have no general-purpose extension CLI; do not alter or append to its ledgers.",
        },
        "yao-bp4-tuning-fairness-p006": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py pilot",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py pilot_extension",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/analyze.py evaluation",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/plot.py",
            ],
            "bounded_extension_commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/run_task.py --stage pilot --index 0",
            ],
            "original_instruction_path": "data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/README.md",
            "budget_note": "Analyze the recorded pilot, extension, and evaluation separately. To run a task, first copy the study to a new identity and use its frozen plan; runners refuse to overwrite retained evidence.",
        },
        "yao-bp4-tuning-selected-validation": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/analyze_fixed.py joint_final",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/assess_stopping.py joint_final",
            ],
            "bounded_extension_commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/run_joint_final_task.py --index 0",
            ],
            "original_instruction_path": "data/reproductions/yao-2312-10950-bp4-tuning-p006/README.md",
            "budget_note": "The selected-validation receipt is a completed fixed cohort. Reuse its task command only after copying the study and freezing a new plan/output identity.",
        },
        "yao-cross-code-plain-baselines": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/assess.py",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/assess.py --render",
            ],
            "bounded_extension_commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/run.py --index 0 --smoke",
            ],
            "original_instruction_path": "data/reproductions/yao-2312-10950-cross-code/README.md",
            "budget_note": "The smoke command is 20 excluded preflight shots in a separate directory, not a new result curve. A production task must use a newly frozen study/plan and must not append to a completed ledger.",
        },
        "yao-cross-code-depolarizing": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/assess.py",
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/assess.py --render",
            ],
            "compute_bearing_extension_commands": [
                "PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/campaign.py pilot",
            ],
            "original_instruction_path": "data/reproductions/yao-2312-10950-cross-code/depolarizing/README.md",
            "budget_note": "The documented pilot freezes 2,000 paired shots per code/rate and dispatches work; use it only in a new study identity and compute allocation. Do not use it to overwrite this completed evidence.",
        },
        "bb72-bpsf-factorial-v2": {
            "kind": "source_command", "study_path": source_path, "decoder_path": None,
            "commands": [
                "OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py preflight",
                "OMP_NUM_THREADS=1 BB72_V2_VERIFY_WORKERS=12 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py report",
            ],
            "compute_bearing_extension_commands": [
                "OMP_NUM_THREADS=1 .venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py run --workers 24",
            ],
            "original_instruction_path": "docs/bb72-bpsf-factorial-v2.md",
            "budget_note": "The frozen factorial has 512 p=.05 and 1,280 p=.08 matched shots per arm. Run only from a new sealed study/output package in a bounded allocation; never rerun into this result directory.",
        },
        "yao-tuned-qbpgd-p006-pilot-n1000": {
            "kind": "retained_result_only", "study_path": source_path, "decoder_path": None,
            "commands": [],
            "bounded_extension_commands": [
                "OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/run.py --code a5 --shots 1000 --seed 20261110 --output /path/to/new/a5-pilot-result",
            ],
            "original_instruction_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/README.md",
            "budget_note": "The retained 1,000-shot seed-20261029 pilot is a separate calibration cohort and must not be pooled with the 10,000-shot confirmation. The fresh-seed command creates a distinct local result only.",
        },
    }
    return recipes.get(dataset_id, {
        "kind": "retained_result_only", "study_path": source_path, "decoder_path": None,
        "commands": [], "original_instruction_path": source_path,
        "budget_note": "No runnable command was found in the retained evidence. Inspect the source record; freeze a new study identity before any extension.",
    })


def _wilson_95(failures: int, shots: int) -> tuple[float, float]:
    """A fixed-shot interval for the retained circuit profiling records."""
    z = 1.959963984540054
    rate = failures / shots
    denominator = 1.0 + z * z / shots
    center = (rate + z * z / (2.0 * shots)) / denominator
    radius = z * ((rate * (1.0 - rate) / shots + z * z / (4.0 * shots * shots)) ** .5) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _circuit_profile_datasets(repository: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose the current canonical circuit CPU profile without relabeling it.

    The current author-v0.2.2 report is one fixed-noise, fixed-shot local
    measurement.  The v1 report intentionally stays provenance only: it used
    the same sampled outcomes while comparing a different native package and
    must not create a second curve or inflate its denominator.
    """
    current_path = "reports/circuit-bp-cpu-profile-author-v022.json"
    prior_path = "reports/circuit-bp-cpu-profile-v1.json"
    report = _read_json(repository / current_path)
    aliases = {
        "rotated_surface_code_memory_X.stim": "relay-surface-d3",
        "bicycle_bivariate_144_12_12_memory_Z.stim": "relay-bb144-memory-z",
        "bb144-memory-z-p005.stim": "beamsearch-bb144-memory-z-p005",
    }
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = {"relay": [], "beamsearch": []}
    for record in report["records"]:
        identifier = aliases.get(record["circuit"])
        if identifier is None:
            # The color-code and BB18 records were useful CPU diagnostics but
            # have no registered public circuit input, so remain in the report.
            continue
        grouped[record["source"]].append((identifier, record))
    datasets: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    decoders: list[dict[str, Any]] = []
    source_papers = {"relay": "relaybp-2506-01779-v2", "beamsearch": "beamsearch-2512-07057-v2"}
    labels = {"relay": "Relay circuit CPU profile", "beamsearch": "BeamSearch circuit CPU profile"}
    for source, records in grouped.items():
        dataset_id = f"circuit-cpu-profile-{source}"
        points: list[dict[str, Any]] = []
        for identifier, record in records:
            failures, shots = int(record["canonical_observable_errors"]), int(record["shots"])
            low, high = _wilson_95(failures, shots)
            point = _point(
                x=0.005, y=failures / shots, n=shots, failures=failures,
                ci_low=low, ci_high=high, status="complete",
                mean_work=float(record["canonical_mean_sweeps"]), work_unit="circuit DEM-BP sweeps",
                mean_seconds=float(record["canonical_decode_seconds"]) / shots,
                metadata={
                    "channel": "embedded_circuit", "physical_rate": 0.005,
                    "metric": "observable_failure_rate", "max_iterations": int(record["max_iterations"]),
                    "canonical_converged": int(record["canonical_converged"]),
                    "canonical_unconverged": shots - int(record["canonical_converged"]),
                    "uncertainty_method": "wilson_score_95_percent_fixed_shots",
                    "denominator_definition": "all fixed profile shots; failure means any observable mismatch",
                    "source_evidence_path": current_path,
                    "prior_comparison_report": prior_path,
                    "claim_limit": report["claim_limit"],
                },
            )
            points.append(point)
            arm = f"circuit-dem-bp-ms-t{record['max_iterations']}-tie-one"
            series.append({"dataset_id": dataset_id, "code_id": identifier, "decoder_id": arm,
                           "label": f"{labels[source]}: {identifier}", "points": [point],
                           "channel_kind": "embedded_circuit"})
        if not points:
            continue
        datasets.append(_dataset(
            dataset_id, label=labels[source], paper_id=source_papers[source],
            evidence_status="local_cpu_profile", source_path=current_path, points=points,
            assets=[_asset(repository, current_path, label="Current canonical CPU profile", kind="json"),
                    _asset(repository, prior_path, label="Prior native-comparison profile (provenance only)", kind="json")],
            caveat="Fixed p=0.005 CPU mechanism/throughput profile. It is a local canonical adapter measurement, not a source curve reproduction. Observable failures and detector convergence remain distinct counters.",
        ))
        arm = "circuit-dem-bp-ms-t8-tie-one"
        decoders.append({"decoder_id": arm, "label": "Detector BP MS", "evidence_status": "local_cpu_profile",
                         "asset": _asset(repository, current_path, label="Exact circuit profile configuration", kind="json"),
                         "configuration": {"source_path": current_path, "settings_status": "fixed_profile_report",
                                           "effective_configuration": {"circuit_profile": True, "family": "circuit_dem_bp",
                                               "check_rule": "min_sum", "message_resolution": "float64",
                                               "max_iterations": 8, "tie_break": "one", "schedule": "flooding",
                                               "numerical_profile": "binary-min-sum-flooding-f64-v1"},
                                           "prior_report": prior_path,
                                           "claim_limit": report["claim_limit"]}})
    return datasets, series, decoders


def build_catalog(repository: Path) -> dict[str, Any]:
    """Build the portable summary catalog from real checked-out evidence only."""
    repository = repository.resolve()
    registry = _read_json(repository / "research/catalog/sources.json")
    datasets, decoders = _presentation_datasets(repository)
    vanilla, _ = _vanilla_dataset(repository)
    tuning, _ = _tuning_dataset(repository)
    cross_code, _ = _cross_code_dataset(repository)
    qbpgd_datasets, qbpgd_series = _qbpgd_datasets(repository)
    non_osd, non_osd_rows = _non_osd_dataset(repository)
    completion, completion_rows, completion_arms = _yao_completion_dataset(repository)
    full_v2, full_v2_rows = _local_curve_dataset(
        repository, dataset_id="pfister-presentation-full-v2-curves", label="Presentation local float64 v2 curves",
        path="from_dr_pfister_presentetations/results/full_v2_curves/comparison.csv", decoder_field="arm", rate_field="ler",
        failures_field="failures", shots_field="shots", lower_field="lower_95_two_sided", upper_field="upper_95_two_sided",
        work_field="mean_work", status="complete")
    ms_curves, ms_rows = _local_curve_dataset(
        repository, dataset_id="pfister-presentation-ms-both-changes", label="Presentation min-sum corrected-policy curves",
        path="from_dr_pfister_presentetations/results/ms_both_changes_curve/comparison.csv", decoder_field="code", rate_field="local_ler",
        failures_field="local_failures", shots_field="shots", lower_field="lower_95", upper_field="upper_95",
        work_field="mean_iterations", status="complete")
    depolarizing_path = "data/reproductions/yao-2312-10950-cross-code/depolarizing/results/all_depolarizing.csv"
    depolarizing_rows = _csv_rows(repository / depolarizing_path)
    depolarizing_points = [_point(x=_number(row["p"]), y=_number(row["rate"]), n=_integer(row["shots"]), failures=_integer(row["failures"]),
                                  ci_low=_number(row["ci95_low"]), ci_high=_number(row["ci95_high"]), status="complete",
                                  mean_work=_number(row["mean_directed_edge_updates"]), work_unit="directed edge updates",
                                  mean_seconds=(_number(row["mean_decode_ms"]) or 0) / 1000,
                                  type_i=_integer(row["type_i"]), type_ii=_integer(row["type_ii"]),
                                  metadata={"channel": row["channel"], "maximum_iterations": _integer(row["T"]),
                                            "source_evidence_path": row["evidence"],
                                            "uncertainty_method": "two_sided_95_percent_binomial_interval",
                                            "denominator_definition": "all terminal shots in the retained result row"})
                          for row in depolarizing_rows]
    depolarizing = _dataset("yao-cross-code-depolarizing", label="Yao four-code depolarizing plain-BP comparison",
                            paper_id="yao-2312-10950-v2", evidence_status="controlled_local_baseline", source_path=depolarizing_path,
                            points=depolarizing_points,
                            assets=[_asset(repository, depolarizing_path, label="All depolarizing results", kind="csv"),
                                    _asset(repository, "data/reproductions/yao-2312-10950-cross-code/depolarizing/decoders.json", label="Frozen policies", kind="decoder_policy")],
                            caveat="Common depolarizing channel but no new source curve is claimed for missing arms.")
    tuning_validation_path = "data/reproductions/yao-2312-10950-bp4-tuning-p006/results/joint_final_results.csv"
    tuning_validation_rows = _csv_rows(repository / tuning_validation_path)
    tuning_validation = _dataset("yao-bp4-tuning-selected-validation", label="A5/B2 selected BP4 validation", paper_id="yao-2312-10950-v2", evidence_status="canonical_tuning_validation", source_path=tuning_validation_path, points=[_point(x=.06, y=_number(r["ler"]), n=_integer(r["shots"]), failures=_integer(r["failures"]), ci_low=_number(r["ci90_lower"]), ci_high=_number(r["ci90_upper"]), status="complete", mean_work=_number(r["mean_iterations"]), work_unit="BP4 iterations", mean_seconds=(_number(r["mean_decode_ms"]) or 0)/1000, type_i=_integer(r["type_i"]), type_ii=_integer(r["type_ii"]), metadata={"confidence_level": 0.90, "uncertainty_method": "two_sided_exact_binomial_interval", "denominator_definition": "fixed validation-shot cohort"}) for r in tuning_validation_rows], assets=[_asset(repository, tuning_validation_path, label="Joint selected validation", kind="csv"), _asset(repository, "data/reproductions/yao-2312-10950-bp4-tuning-p006/results/joint_final_results.json", label="Joint validation receipt", kind="json")], caveat="Selection/validation evidence is distinct from equal-work fairness.")
    circuit_datasets, circuit_series, _ = _circuit_profile_datasets(repository)
    datasets.extend([vanilla, tuning, tuning_validation, cross_code, non_osd, *qbpgd_datasets, full_v2, ms_curves, depolarizing, *circuit_datasets])
    bb72_datasets, bb72_series, _ = _bb72_datasets(repository)
    datasets.extend(bb72_datasets)
    experiments = [
        {"experiment_id": "fair-beam-relay-css-v2", "dataset_id": "bb72-fair-beam-relay-v2", "paper_ids": ["relaybp-2506-01779-v2", "beamsearch-2512-07057-v2"],
         "evidence_status": "controlled_css_adaptation", "reproduction_recipe": {"kind": "registered_study", "study_path": "data/studies/fair-beam-relay-css-v2.json", "decoder_path": "examples/bb72-relay-decoder.toml", "argv": ["bp-registry", "data/studies/fair-beam-relay-css-v2.json", "--decoder", "examples/bb72-relay-decoder.toml", "--workers", "8"], "budget_note": "The registered command may run the frozen campaign if its complete package is absent; do not use it as a casual preview."}},
        {"experiment_id": "yao-vanilla", "dataset_id": "yao-vanilla-a5-b2", "paper_ids": ["yao-2312-10950-v2"], "evidence_status": "canonical_adaptation", "reproduction_recipe": {"kind": "source_command", "study_path": "data/reproductions/yao-2312-10950-vanilla/campaign.json", "decoder_path": "data/reproductions/yao-2312-10950-vanilla/decoders/bp4_v2.json", "commands": ["PYTHONPATH=src python data/reproductions/yao-2312-10950-vanilla/analyze.py"], "budget_note": "Inspect/analyze retained evidence only; task execution uses frozen shard indices and must not overwrite ledgers."}},
        {"experiment_id": "yao-non-osd", "dataset_id": "yao-non-osd-results", "paper_ids": ["yao-2312-10950-v2"], "evidence_status": "source_informed_canonical_adaptation", "reproduction_recipe": {"kind": "source_command", "study_path": "data/reproductions/yao-2312-10950-non-osd/source_points.json", "decoder_path": None, "commands": ["PYTHONPATH=src python data/reproductions/yao-2312-10950-non-osd/assess.py"], "budget_note": "Assessment replays retained ledgers; new points require a separately frozen bounded plan."}},
        {"experiment_id": "yao-qbpgd-tuned", "dataset_id": "yao-tuned-qbpgd-p006", "paper_ids": ["yao-2312-10950-v2"], "evidence_status": "canonical_adaptation", "reproduction_recipe": {"kind": "source_command", "study_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/README.md", "decoder_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/decoders/a5.json", "commands": ["PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/run.py --code a5 --shots 10000 --seed 20261030 --output NEW_DIRECTORY"], "budget_note": "The runner refuses overwrite; command is a compute-bearing exact recipe, not a browser action."}},
        {"experiment_id": "yao-qbpgd-tuned-pilot-n1000", "dataset_id": "yao-tuned-qbpgd-p006-pilot-n1000", "paper_ids": ["yao-2312-10950-v2"], "evidence_status": "canonical_adaptation", "reproduction_recipe": {"kind": "retained_result_only", "study_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/results", "decoder_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/decoders/a5.json", "commands": [], "bounded_extension_commands": ["OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/run.py --code a5 --shots 1000 --seed 20261110 --output /path/to/new/a5-pilot-result"], "original_instruction_path": "data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/README.md", "budget_note": "Exploratory 1,000-shot cohort retained for provenance. Do not pool it with or present it as the 10,000-shot confirmation run; the fresh-seed extension is a distinct result and is never pooled."}},
    ]
    if completion:
        datasets.append(completion)
        experiments.append({
            "experiment_id": _YAO_COMPLETION_DATASET, "dataset_id": _YAO_COMPLETION_DATASET,
            "paper_ids": ["yao-2312-10950-v2"], "evidence_status": completion["evidence_status"],
            "reproduction_recipe": {
                "kind": "source_command", "study_path": f"{_YAO_COMPLETION}/plan.json",
                "decoder_path": f"{_YAO_COMPLETION}/plan.json",
                "commands": [f"PYTHONPATH=src .venv/bin/python {_YAO_COMPLETION}/run.py --collect"],
                "original_instruction_path": f"{_YAO_COMPLETION}/README.md",
                "budget_note": "Collection verifies retained terminal ledgers. Point execution follows the frozen plan.",
            },
        })
    by_id = {dataset["dataset_id"]: dataset for dataset in datasets}
    series: list[dict[str, Any]] = []
    series += _grouped_series("pfister-presentation-source-curves", by_id["pfister-presentation-source-curves"]["points"],
                              _csv_rows(repository / "from_dr_pfister_presentetations/results/source_curves.csv"),
                              code_field="code", decoder_field="decoder", label_prefix="Presentation transcription")
    series += _grouped_series("pfister-presentation-local-pilots", by_id["pfister-presentation-local-pilots"]["points"],
                              _csv_rows(repository / "from_dr_pfister_presentetations/results/pilot_summary.csv"),
                              code_field="code", decoder_field="decoder", label_prefix="Presentation pilot")
    series += _grouped_series("yao-vanilla-a5-b2", by_id["yao-vanilla-a5-b2"]["points"],
                              _csv_rows(repository / "data/reproductions/yao-2312-10950-vanilla/results/comparison.csv"),
                              code_field="code", decoder_field="arm", label_prefix="Yao vanilla")
    series += _grouped_series("yao-bp4-tuning-fairness-p006", by_id["yao-bp4-tuning-fairness-p006"]["points"],
                              _csv_rows(repository / "data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/evaluation_results.csv"),
                              code_field="code", decoder_field="candidate_id", label_prefix="BP4 fairness")
    series += _grouped_series("yao-bp4-tuning-selected-validation", tuning_validation["points"], tuning_validation_rows,
                              code_field="code", decoder_field="candidate_id", label_prefix="BP4 selected validation")
    series += _grouped_series("yao-cross-code-plain-baselines", by_id["yao-cross-code-plain-baselines"]["points"],
                              _csv_rows(repository / "data/reproductions/yao-2312-10950-cross-code/results/performance.csv"),
                              code_field="code", decoder_field="decoder", label_prefix="Cross-code baseline")
    series += _grouped_series("yao-non-osd-results", by_id["yao-non-osd-results"]["points"], non_osd_rows,
                              code_field="code", decoder_field="curve", label_prefix="Yao non-OSD", scope_field="figure")
    series += _grouped_series("pfister-presentation-full-v2-curves", full_v2["points"], full_v2_rows,
                              code_field="code", decoder_field="arm", label_prefix="Presentation float64 v2")
    for row in ms_rows:
        row["decoder_id"] = "bp4_ms_both_changes"
    series += _grouped_series("pfister-presentation-ms-both-changes", ms_curves["points"], ms_rows,
                              code_field="code", decoder_field="decoder_id", label_prefix="Presentation min-sum")
    series += _grouped_series("yao-cross-code-depolarizing", depolarizing["points"], depolarizing_rows,
                              code_field="code", decoder_field="decoder", label_prefix="Cross-code depolarizing")
    if completion:
        for item in _grouped_series(_YAO_COMPLETION_DATASET, completion["points"], completion_rows,
                                    code_field="code", decoder_field="arm", label_prefix="Direct completion"):
            item["channel_kind"] = completion_arms[f'{item["code_id"]}:{item["decoder_id"]}']["noise_model"]
            series.append(item)
    series.extend(qbpgd_series)
    series.extend(bb72_series)
    series.extend(circuit_series)
    presentation_v2_files = {
        "binary_tuned_oms_q8": "binary_tuned_oms.json",
        "binary_tuned_spa_v2": "canonical_binary_spa_f64_v2.json",
        "bp4_tuned_sp_v2": "canonical_bp4_f64_v2.json",
        "bp4_vanilla_ms_q8": "bp4_vanilla_ms.json",
        "bp4_vanilla_sp_v2": "canonical_bp4_f64_v2.json",
    }

    def policy_source(dataset_id: str, code_id: str, arm_id: str) -> tuple[str, str]:
        """Return the arm's exact policy/config source, never a default fallback."""
        if dataset_id == "yao-vanilla-a5-b2":
            return (f"data/reproductions/yao-2312-10950-vanilla/decoders/{arm_id}.json", "exact_policy_file")
        if dataset_id == "pfister-presentation-local-pilots":
            return (f"from_dr_pfister_presentetations/decoders/{arm_id}.json", "exact_policy_file")
        if dataset_id == "pfister-presentation-full-v2-curves":
            filename = presentation_v2_files.get(arm_id)
            return ((f"from_dr_pfister_presentetations/decoders/{filename}" if filename else
                     "from_dr_pfister_presentetations/results/full_v2_curves/comparison.csv"),
                    ("numerical_profile_with_runner_overrides" if arm_id in {"bp4_tuned_sp_v2", "bp4_vanilla_sp_v2"} else "exact_policy_file") if filename else "settings_unavailable")
        if dataset_id == "pfister-presentation-ms-both-changes":
            return ("from_dr_pfister_presentetations/decoders/bp4_ms_both_changes_diagnostic.json", "exact_policy_file")
        if dataset_id == "pfister-presentation-source-curves":
            return ("from_dr_pfister_presentetations/results/source_curves.csv", "source_values_only_settings_unavailable")
        if dataset_id in {"yao-bp4-tuning-fairness-p006", "yao-bp4-tuning-selected-validation"}:
            return ("data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/evaluation_candidates.json" if dataset_id.endswith("fairness-p006") else
                    "data/reproductions/yao-2312-10950-bp4-tuning-p006/decoders/joint_final_candidates.json", "exact_candidate_receipt")
        if dataset_id in {"yao-cross-code-plain-baselines", "yao-cross-code-depolarizing"}:
            root = "data/reproductions/yao-2312-10950-cross-code"
            return (f"{root}/decoders.json" if dataset_id.endswith("baselines") else f"{root}/depolarizing/decoders.json", "exact_study_policy_file")
        if dataset_id == _YAO_COMPLETION_DATASET:
            return (f"{_YAO_COMPLETION}/plan.json", "exact_campaign_arm")
        if dataset_id == "yao-non-osd-results":
            if arm_id == "qbp":
                # assess.prior_qbp_runs / verified_qbp_followups inherit the
                # frozen vanilla BP4 v2 arm, not run_point's Q-BPGD controller.
                return ("data/reproductions/yao-2312-10950-vanilla/decoders/bp4_v2.json", "inherited_vanilla_policy_file")
            return ("data/reproductions/yao-2312-10950-non-osd/run_point.py", "policy_fixed_in_runner")
        if dataset_id in {"yao-tuned-qbpgd-p006", "yao-tuned-qbpgd-p006-pilot-n1000"}:
            return (f"data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/decoders/{code_id}.json", "exact_code_policy_file")
        if dataset_id == "bb72-fair-beam-relay-v2":
            return ("data/results/fair-beam-relay-css-v2/result.json", "effective_selected_configuration_in_verified_result")
        if dataset_id == "bb72-bpsf-factorial-v2":
            return ("data/studies/bb72-bpsf-factorial-v2.json", "exact_study_configuration")
        if dataset_id.startswith("circuit-cpu-profile-"):
            return ("reports/circuit-bp-cpu-profile-author-v022.json", "fixed_profile_report")
        raise ValueError(f"no policy source mapping for {dataset_id}")

    fair_design = _read_json(repository / "data/studies/fair-beam-relay-css-v2.json")
    bpsf_design = _read_json(repository / "data/studies/bb72-bpsf-factorial-v2.json")

    def effective_configuration(dataset_id: str, arm_id: str) -> dict[str, Any] | None:
        """Materialize per-arm controls from the immutable design/result records."""
        if dataset_id == "pfister-presentation-full-v2-curves" and arm_id in {"bp4_tuned_sp_v2", "bp4_vanilla_sp_v2"}:
            runner_path = "from_dr_pfister_presentetations/run_full_v2_curve.py"
            return {"family": "bp4", "numerical_profile": "quaternary-bp4-f64-v2",
                    "message_resolution": "float64", "check_rule": "sum_product", "check_cap": None,
                    "product_epsilon": 1e-10, "v2c_damping": 0.0 if arm_id == "bp4_vanilla_sp_v2" else 0.1,
                    "hard_decision": "strict_I_then_X_then_Z_else_Y", "zero_syndrome_shortcut": False,
                    "prior": "depolarizing_joint_p0_equals_physical_p", "max_iterations": 1000,
                    "stop": "first_completed_syndrome_match", "runner_path": runner_path,
                    "runner_sha256": sha256((repository / runner_path).read_bytes()).hexdigest(),
                    "binding": "Float64 arm implemented by the full-v2 runner; the Q8 source configuration is a separate comparison."}
        if dataset_id == "bb72-fair-beam-relay-v2":
            method, gamma_token, profile = arm_id.split("-", 2)
            gamma = int(gamma_token.removeprefix("g")) / 1000
            if gamma not in fair_design["damping_gammas"] or profile not in fair_design["profiles"]:
                raise ValueError(f"unknown fair BB72 effective arm {arm_id}")
            return {
                "method": method,
                "damping_gamma": gamma,
                "selected_profile": profile,
                "profile_controls": fair_design["profiles"][profile],
                "common_controls": fair_design["common_controls"],
                "noise_model": fair_design["noise_model"],
                "selection_rule": fair_design["selection_rule"],
                "selection_evidence_path": "data/results/fair-beam-relay-css-v2/result.json",
            }
        if dataset_id == "bb72-bpsf-factorial-v2":
            update_token, gamma_token, mode = arm_id.split("-", 2)
            update = {"spa": "binary_spa", "ms": "min_sum"}.get(update_token)
            gamma = int(gamma_token.removeprefix("g")) / 1000
            if update not in bpsf_design["factorial"]["update"] or gamma not in bpsf_design["factorial"]["damping_gamma"] or mode not in bpsf_design["factorial"]["mode"]:
                raise ValueError(f"unknown BPSF BB72 effective arm {arm_id}")
            mode_controls: dict[str, Any] = {"mode": mode}
            if mode == "bp20":
                mode_controls["bp_sweeps"] = 20
            elif mode == "bp40":
                mode_controls["bp_sweeps"] = 40
            else:
                mode_controls["bpsf_controls"] = bpsf_design["factorial"]["bpsf_controls"]
            return {
                "update": update,
                "damping_gamma": gamma,
                **mode_controls,
                "shared_work": bpsf_design["shared_work"],
                "channel": bpsf_design["channel"],
                "cohort": bpsf_design["cohort"],
            }
        if dataset_id.startswith("circuit-cpu-profile-"):
            return {"circuit_profile": True, "family": "circuit_dem_bp", "check_rule": "min_sum",
                    "message_resolution": "float64", "max_iterations": 8, "tie_break": "one",
                    "schedule": "flooding", "numerical_profile": "binary-min-sum-flooding-f64-v1",
                    "claim_scope": "local_cpu_profile"}
        return None

    # Raw arm names collide across studies.  A series therefore names both its
    # study and code; the record carries the original arm name and exact file.
    for item in series:
        raw_arm = item["decoder_id"]
        identity_arm = raw_arm if item.get("decoder_identity_scope") is None else f"{raw_arm}@{item['decoder_identity_scope']}"
        raw_code = item["code_id"]
        source, setting_status = policy_source(item["dataset_id"], raw_code, raw_arm)
        item["source_decoder_id"] = raw_arm
        item["decoder_id"] = f"{item['dataset_id']}:{raw_code}:{identity_arm}"
        configuration: dict[str, Any] = {"source_path": source, "source_arm_id": raw_arm,
                                         "settings_status": setting_status}
        if "series_scope" in item:
            configuration["identity_scope"] = item["series_scope"]
        exact_configuration = (completion_arms[f"{raw_code}:{raw_arm}"]
                               if item["dataset_id"] == _YAO_COMPLETION_DATASET
                               else effective_configuration(item["dataset_id"], raw_arm))
        if exact_configuration is not None:
            configuration["effective_configuration"] = exact_configuration
        candidate_source = repository / source
        if candidate_source.suffix == ".json" and candidate_source.exists():
            candidate_document = _read_json(candidate_source)
            candidates = candidate_document.get("candidates") if isinstance(candidate_document, dict) else None
            if isinstance(candidates, list):
                candidate = next((value for value in candidates if value.get("id") == raw_arm), None)
                if candidate is not None:
                    configuration["effective_candidate"] = candidate
                elif setting_status == "exact_candidate_receipt":
                    raise ValueError(f"candidate {raw_arm} missing from {source}")
            elif setting_status in {"exact_policy_file", "inherited_vanilla_policy_file"}:
                configuration["effective_policy"] = candidate_document
                if setting_status == "inherited_vanilla_policy_file":
                    configuration["inherited_binding"] = {"dataset_id": "yao-vanilla-a5-b2", "decoder_arm": "bp4_v2",
                        "analysis_path": "data/reproductions/yao-2312-10950-non-osd/assess.py"}
            elif setting_status == "exact_code_policy_file":
                if candidate_document.get("code") != raw_code:
                    raise ValueError(f"Q-BPGD source/code mismatch for {raw_code} in {source}")
                arm_policy = candidate_document.get(raw_arm)
                if not isinstance(arm_policy, dict):
                    raise ValueError(f"Q-BPGD arm {raw_arm} missing from {source}")
                selected_path = candidate_document["selected_bp4_path"]
                if sha256((repository / selected_path).read_bytes()).hexdigest() != candidate_document["selected_bp4_sha256"]:
                    raise ValueError(f"selected Q-BPGD BP4 checksum mismatch for {raw_code}")
                selected_candidates = _read_json(repository / selected_path).get("candidates", [])
                selected = next((candidate for candidate in selected_candidates
                                 if candidate.get("id") == candidate_document.get("selected_candidate_id")), None)
                if selected is None:
                    raise ValueError(f"selected Q-BPGD candidate missing for {raw_code}")
                configuration["effective_configuration"] = {
                    "selected_arm": raw_arm, "arm_policy": arm_policy, "controller": candidate_document["qbpgd"],
                    "physical_p": candidate_document["physical_p"], "code_semantic_sha256": candidate_document["code_semantic_sha256"],
                    "selected_bp4": {"candidate_id": candidate_document["selected_candidate_id"],
                                     "path": candidate_document["selected_bp4_path"],
                                     "sha256": candidate_document["selected_bp4_sha256"], "candidate": selected},
                }
            elif setting_status == "exact_study_policy_file":
                metadata = [point.get("metadata", {}) for point in item["points"]]
                channels = {value.get("channel") for value in metadata if value.get("channel") is not None}
                iterations = {value.get("maximum_iterations") for value in metadata if value.get("maximum_iterations") is not None}
                if len(channels) != 1 or len(iterations) != 1:
                    raise ValueError(f"ambiguous cross-code point binding for {item['decoder_id']}")
                if candidate_document.get("max_iterations") != next(iter(iterations)):
                    raise ValueError(f"cross-code iteration policy mismatch for {item['decoder_id']}")
                configuration["effective_configuration"] = {
                    "selected_arm": raw_arm, "shared_policy": candidate_document,
                    "channel_binding": next(iter(channels)), "maximum_iterations": next(iter(iterations)),
                    "arm_binding_basis": "selected_arm and channel are retained result-row fields; policy values are shared by the source document",
                }
        decoders.append({"decoder_id": item["decoder_id"], "label": item["label"],
                         "evidence_status": by_id[item["dataset_id"]]["evidence_status"],
                         "asset": _asset(repository, source, label="Exact configuration source", kind="decoder_source"),
                         "configuration": configuration})
    code_aliases = {"B1_882_24": "b1", "double_Gross_288_12_18": "double-gross", "double_gross": "double-gross", "BB72": "bb72"}
    for item in series:
        item["source_code_label"] = item["code_id"]
        item["code_id"] = code_aliases.get(item["code_id"], item["code_id"])
        if "channel_kind" not in item:
            dataset_id = item["dataset_id"]
            if dataset_id.startswith("circuit-cpu-profile-"):
                item["channel_kind"] = "embedded_circuit"
            elif dataset_id in {"yao-cross-code-plain-baselines", "yao-non-osd-results"}:
                item["channel_kind"] = "depolarizing" if item["code_id"] in {"a5", "b2"} else "x_only"
            elif dataset_id in {"bb72-fair-beam-relay-v2", "bb72-bpsf-factorial-v2"}:
                item["channel_kind"] = "x_only"
            else:
                item["channel_kind"] = "depolarizing"
    grouped_all_series: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in series:
        scope_key = json.dumps(item.get("series_scope", {}), sort_keys=True, separators=(",", ":"))
        key = (item["dataset_id"], item["code_id"], item["decoder_id"], scope_key)
        prior = grouped_all_series.get(key)
        if prior is None:
            grouped_all_series[key] = {**item, "points": list(item["points"])}
        else:
            prior["points"].extend(item["points"])
    series = []
    for key, item in sorted(grouped_all_series.items()):
        item["points"].sort(key=lambda point: (point["x"], point["n"] or -1))
        item["series_id"] = "series-" + sha256("\x1f".join(key).encode("utf-8")).hexdigest()[:16]
        series.append(item)
    from .inputs import input_catalog, input_registry
    codes, circuits = input_catalog(repository, _asset)
    existing_experiments = {item["dataset_id"] for item in experiments if item.get("dataset_id")}
    for dataset in datasets:
        if dataset["dataset_id"] in existing_experiments:
            continue
        members = [item for item in series if item["dataset_id"] == dataset["dataset_id"]]
        experiments.append({"experiment_id": f"catalog-{dataset['dataset_id']}", "dataset_id": dataset["dataset_id"],
                            "dataset_ids": [dataset["dataset_id"]], "code_ids": sorted({item["code_id"] for item in members}),
                            "decoder_ids": sorted({item["decoder_id"] for item in members}), "paper_ids": dataset.get("paper_ids", [dataset["paper_id"]]),
                            "description": dataset["caveat"], "evidence_status": dataset["evidence_status"],
                            "reproduction_recipe": _fallback_recipe(dataset["dataset_id"], dataset["source_path"])})
    for experiment in experiments:
        dataset_id = experiment.get("dataset_id")
        if dataset_id is None:
            continue
        members = [item for item in series if item["dataset_id"] == dataset_id]
        experiment.setdefault("dataset_ids", [dataset_id])
        experiment.setdefault("code_ids", sorted({item["code_id"] for item in members}))
        experiment.setdefault("decoder_ids", sorted({item["decoder_id"] for item in members}))
        experiment.setdefault("description", by_id[dataset_id]["caveat"])
    # Helper collections may have supplied a legacy unqualified record before
    # the series pass created the authoritative namespaced record.  Keep one
    # entity per ID, preferring the final exact arm-specific mapping.
    unique_decoders: dict[str, dict[str, Any]] = {}
    for decoder in decoders:
        unique_decoders[decoder["decoder_id"]] = decoder
    decoders = list(unique_decoders.values())
    catalog = {"schema_version": 1, "catalog_kind": "retained_research_evidence", "papers": registry["papers"],
            "studies": _study_records(repository, registry), "experiments": experiments, "decoders": decoders,
            "codes": codes, "circuits": circuits, "channels": input_registry(repository)["channels"], "datasets": datasets, "result_series": series,
            "limitations": ["Raw per-shot ledgers are never exported as though tracked when a study marks them local_only.", "A source transcription, canonical adaptation, and source-faithful result are distinct evidence statuses."]}
    from .catalog_model import extend_catalog
    return extend_catalog(catalog, registry, repository)


def write_catalog(repository: Path, destination: Path) -> dict[str, Any]:
    """Write a deterministic JSON snapshot and return the in-memory catalog."""
    catalog = build_catalog(repository)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return catalog
