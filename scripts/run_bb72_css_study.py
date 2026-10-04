#!/usr/bin/env python3
"""Sealed, matched BB72 CSS BP comparison through the public canonical runner."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import sys
from typing import Any

from scipy.stats import beta, binomtest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.cli import run_canonical, verify_run  # noqa: E402
from bp_registry.ledger import read_canonical_events  # noqa: E402
from bp_registry.manifests import preflight  # noqa: E402


DESIGN = ROOT / "data/studies/bb72-css-bp-v1.json"
BB72_BASE = ROOT / "data/manifests/phase3-pilot-bb72.json"
B1_BASE = ROOT / "data/manifests/phase5-b1-mechanism-pilot.json"
OUTPUT = ROOT / "data/results/bb72-css-bp-v1"
CODE_FILES = tuple(sorted(str(path.relative_to(ROOT)) for path in (ROOT / "src/bp_registry").rglob("*.py"))) + (
    "data/manifests/phase3-pilot-bb72.json",
    "data/manifests/phase5-b1-mechanism-pilot.json",
    "scripts/run_bb72_css_study.py",
)
VALID = frozenset(("exact", "stabilizer_equivalent"))


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_once(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"sealed file differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def design() -> dict[str, Any]:
    value = _read(DESIGN)
    if value.get("study_id") != "bb72-css-bp-v1" or value.get("status") != "prespecified_before_study_sampling":
        raise ValueError("unexpected BB72 study design")
    if _digest(ROOT / value["artifact"]["path"]) != value["artifact"]["raw_sha256"]:
        raise ValueError("BB72 artifact differs from frozen design")
    rates = value["channel"]["x_error_rates"]
    if rates != [0.03, 0.05, 0.08] or len(set(rates)) != len(rates):
        raise ValueError("frozen noise grid differs")
    work = value["shared_work"]
    if work["edge_count"] != 216 or work["max_bp_sweeps_per_shot"] != 40:
        raise ValueError("frozen shared work differs")
    if work["max_check_to_variable_updates_per_shot"] != 40 * 216 or work["max_variable_to_check_updates_per_shot"] != 40 * 216:
        raise ValueError("edge message cap differs from frozen graph and sweep envelope")
    selection, evaluation = value["cohorts"]["selection"], value["cohorts"]["evaluation"]
    if selection["identity_prefix"] == evaluation["identity_prefix"] or selection["sample_seed"] == evaluation["sample_seed"]:
        raise ValueError("selection and evaluation samples are not separated")
    if selection["shots_per_rate"] != 128 or evaluation["shots_per_rate"] != 512:
        raise ValueError("frozen sample counts differ")
    if tuple(item["id"] for item in value["families"]) != ("spa", "ms", "nms", "oms", "bpgd", "bpsf"):
        raise ValueError("decoder cohort differs")
    return value


def configurations(spec: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    spec = design() if spec is None else spec
    output: list[dict[str, Any]] = []
    for family in spec["families"]:
        parameters = ("alpha", "offset", "gamma")
        names = [name for name in parameters if name in family]
        for values in product(*(family[name] if isinstance(family[name], list) else [family[name]] for name in names)):
            config = {"family": family["id"], "kind": family["kind"], **dict(zip(names, values, strict=True))}
            parts = [family["id"]] + [f"{name[0]}{int(round(value * 1000)):04d}" for name, value in zip(names, values, strict=True)]
            config["id"] = "-".join(parts)
            output.append(config)
    if len(output) != 17 or len({item["id"] for item in output}) != 17:
        raise ValueError("frozen parameter grid differs")
    return output


def _rate_id(rate: float) -> str:
    return f"p{int(round(rate * 1000)):03d}"


def _physical_id(spec: dict[str, Any], cohort: str, rate: float) -> str:
    return f"{spec['cohorts'][cohort]['identity_prefix']}-{_rate_id(rate)}"


def _memory(gamma: float) -> dict[str, Any]:
    return {"bindings": [{
        "binding_id": "v2c-damping", "kind": "v2c_damping", "target": "v2c",
        "parameters": {"gamma": gamma}, "order": 0,
        "history_owner": "attempt:v2c-damping", "state_lifetime": "attempt",
        "advance_boundary": "source_iteration", "refresh_boundary": "attempt_start",
        "source_status": "canonical_adaptation", "retain_history": False,
    }]}


def _apply_budgets(manifest: dict[str, Any], spec: dict[str, Any], cohort: str) -> None:
    manifest["budgets"]["max_shots"] = spec["cohorts"][cohort]["shots_per_rate"]
    work = spec["shared_work"]
    for scope in ("shot", "search", "attempt"):
        budget = manifest["budgets"][scope]
        budget["max_iterations"] = work["max_bp_sweeps_per_shot"]
        caps = budget["work_limits"]
        caps["check_to_variable_updates"] = work["max_check_to_variable_updates_per_shot"]
        caps["variable_to_check_updates"] = work["max_variable_to_check_updates_per_shot"]
        caps["belief_assemblies"] = 8640
        caps["candidate_checks"] = 8640
        caps["bp_calls"] = 32
    if "intervention_limits" in manifest:
        caps = manifest["intervention_limits"]["work_caps"]
        caps.update(manifest["budgets"]["attempt"]["work_limits"])
        manifest["intervention_limits"]["max_runtime_seconds"] = 300.0


def make_manifest(spec: dict[str, Any], config: dict[str, Any], cohort: str, rate: float) -> dict[str, Any]:
    if cohort not in ("selection", "evaluation") or rate not in spec["channel"]["x_error_rates"]:
        raise ValueError("unregistered cohort or rate")
    family = config["family"]
    if config not in configurations(spec):
        raise ValueError("configuration is outside the frozen grid")
    if family in ("bpgd", "bpsf"):
        stage = _read(B1_BASE)
        arm = "guided_decimation" if family == "bpgd" else "syndrome_flip"
        manifest = deepcopy(stage["arm_manifests"][arm])
        manifest["artifact"] = deepcopy(_read(BB72_BASE)["artifact"])
        manifest["schema_version"] = 6
        manifest["memory"] = _memory(config["gamma"])
        control = manifest["intervention"]
        frozen = next(item for item in spec["families"] if item["id"] == family)
        for field in ("round_limit", "sweeps_per_round", "baseline_sweeps", "attempt_sweeps", "test_cap", "top_k", "max_weight"):
            if field in frozen:
                control[field] = frozen[field]
        if control.get("root_seed") is not None:
            control["root_seed"] = f"{spec['study_id']}-{cohort}-{_rate_id(rate)}-decoder"
    else:
        manifest = deepcopy(_read(BB72_BASE))
        manifest["schema_version"] = 4
        manifest["memory"] = _memory(config["gamma"])
        update = manifest["policies"]["update"]
        update["kind"] = config["kind"]
        update["binding_id"] = {
            "binary_spa": "update-binary-spa-v1", "min_sum": "update-min-sum-v1",
            "normalized_min_sum": "update-normalized-min-sum-v1", "offset_min_sum": "update-offset-min-sum-v1",
        }[config["kind"]]
        if config["kind"] != "binary_spa":
            manifest["numerical_profile"] = "cpu-float64-min-sum-v1"
        if "alpha" in config or "offset" in config:
            update["parameter_assignment"] = {"shape": "scalar", "value": config.get("alpha", config.get("offset"))}
    _apply_budgets(manifest, spec, cohort)
    manifest["run_id"] = f"{spec['study_id']}-{cohort}-{_rate_id(rate)}-{config['id']}"
    manifest["error_rate"] = rate
    manifest["randomness"].update({
        "sample_seed": spec["cohorts"][cohort]["sample_seed"],
        "physical_sample_identity": _physical_id(spec, cohort, rate),
        "decoder_seed_identity": f"{spec['study_id']}-{cohort}-{_rate_id(rate)}-decoder",
    })
    manifest["evidence"] = {
        "relation": "canonical_implemented", "fixture": "development_fixture", "assessment_status": "not_assessed",
        "procedure": f"BB72 controlled CSS comparison; {cohort}; {_rate_id(rate)}; {config['id']}; frozen design sha256:{_digest(DESIGN)}",
        "sources": ["Bravyi et al. arXiv:2308.07915; pinned BB72 construction", "Yao et al. arXiv:2312.10950v2" if family == "bpgd" else "BP-SF arXiv:2507.00254v1" if family == "bpsf" else "Gokduman et al. arXiv:2411.08177v2 Eq. 17"],
        "discrepancies": ["BB72 X-only code-capacity execution is not the Bravyi circuit-level BP-OSD experiment.", "Source-defined interventions and damping are controlled BB72 adaptations, not source-curve reproductions."],
    }
    resolved = preflight(manifest).manifest
    if resolved.artifact.code_id != "bravyi-bb-72" or resolved.budgets.max_shots != spec["cohorts"][cohort]["shots_per_rate"]:
        raise ValueError("BB72 preflight changed the intended code or sample count")
    return manifest


def _seal() -> dict[str, Any]:
    return {"schema_version": 1, "study_id": "bb72-css-bp-v1", "design_sha256": _digest(DESIGN),
            "implementation_sha256": {name: _digest(ROOT / name) for name in CODE_FILES}}


def check_seal() -> dict[str, Any]:
    expected = _seal()
    path = OUTPUT / "seal.json"
    if not path.exists() and OUTPUT.exists() and any(OUTPUT.rglob("events.jsonl")):
        raise ValueError("study evidence exists without its presampling implementation seal")
    _write_once(path, _bytes(expected))
    return expected


def _arm_path(cohort: str, rate: float, config: dict[str, Any]) -> Path:
    return OUTPUT / cohort / _rate_id(rate) / config["id"]


def _prepare_arm(spec: dict[str, Any], config: dict[str, Any], cohort: str, rate: float) -> tuple[Path, Path]:
    root = _arm_path(cohort, rate, config)
    path = root / "manifest.json"
    _write_once(path, _bytes(make_manifest(spec, config, cohort, rate)))
    return path, root


def _selection_arms(spec: dict[str, Any]) -> list[tuple[str, float, dict[str, Any]]]:
    return [("selection", rate, config) for rate in spec["channel"]["x_error_rates"] for config in configurations(spec)]


def _evaluation_arms(spec: dict[str, Any], lock: dict[str, Any]) -> list[tuple[str, float, dict[str, Any]]]:
    by_id = {item["id"]: item for item in configurations(spec)}
    ids = ["spa-g1000", *lock["selected_configuration_ids"].values()]
    chosen = [by_id[key] for key in dict.fromkeys(ids)]
    return [("evaluation", rate, config) for rate in spec["channel"]["x_error_rates"] for config in chosen]


def prepare(cohort: str) -> list[tuple[Path, Path]]:
    spec = design()
    check_seal()
    arms = _selection_arms(spec) if cohort == "selection" else _evaluation_arms(spec, selection_lock())
    return [_prepare_arm(spec, config, arm_cohort, rate) for arm_cohort, rate, config in arms]


def _execute_arm(paths: tuple[Path, Path]) -> str:
    manifest, root = paths
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("study requires OMP_NUM_THREADS=1 per process")
    run_canonical(manifest, root)
    verified = verify_run(root)
    if verified["final_row_count"] != _read(manifest)["budgets"]["max_shots"]:
        raise ValueError(f"incomplete verified arm: {root}")
    print(f"verified {root.relative_to(OUTPUT)}", flush=True)
    return str(root)


def run(cohort: str, workers: int | None = None) -> list[str]:
    arms = prepare(cohort)
    count = min(len(arms), workers or int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1)))
    if count < 1:
        raise ValueError("worker count must be positive")
    with ProcessPoolExecutor(max_workers=count) as pool:
        return list(pool.map(_execute_arm, arms))


def _terminals(root: Path) -> dict[int, dict[str, Any]]:
    result = verify_run(root)
    manifest = _read(root / "manifest.json")
    if result["final_row_count"] != manifest["budgets"]["max_shots"]:
        raise ValueError(f"verified arm is incomplete: {root}")
    starts: dict[int, str] = {}
    terminals: dict[int, dict[str, Any]] = {}
    for event in read_canonical_events(root / "events.jsonl"):
        if event["kind"] == "shot_begin":
            shot_id = event["shot_id"]
            if shot_id in starts:
                raise ValueError("duplicate shot beginning")
            starts[shot_id] = event["sample_seed_identity"]
        elif event["kind"] == "termination":
            shot_id = event["shot_id"]
            if shot_id in terminals:
                raise ValueError("duplicate terminal")
            data = event["data"]
            payload = data.get("payload", data)
            runtime = data.get("decode_runtime")
            terminals[shot_id] = {
                "outcome": payload.get("outcome"), "termination": event["termination"],
                "work_vector": payload["work_vector"],
                "converged": payload.get("converged"),
                "decode_runtime_ns": runtime.get("value") if isinstance(runtime, dict) and runtime.get("unit") == "ns" else None,
            }
    expected = set(range(manifest["budgets"]["max_shots"]))
    if set(starts) != expected or set(terminals) != expected:
        raise ValueError("missing physical or terminal shots")
    for shot_id, row in terminals.items():
        row["sample_identity"] = starts[shot_id]
    return terminals


def _verified_group(spec: dict[str, Any], cohort: str, rate: float, configs: list[dict[str, Any]]) -> dict[str, dict[int, dict[str, Any]]]:
    paths = [_arm_path(cohort, rate, config) for config in configs]
    requested = int(os.environ.get("BB72_VERIFY_WORKERS", os.environ.get("SLURM_CPUS_PER_TASK", "8")))
    if requested < 1:
        raise ValueError("BB72_VERIFY_WORKERS must be positive")
    with ProcessPoolExecutor(max_workers=min(len(configs), requested)) as pool:
        terminal_sets = list(pool.map(_terminals, paths))
    group = {config["id"]: rows for config, rows in zip(configs, terminal_sets, strict=True)}
    identities = [tuple(group[key][shot]["sample_identity"] for shot in sorted(group[key])) for key in group]
    if any(other != identities[0] for other in identities[1:]):
        raise ValueError(f"mismatched physical samples: {cohort} {_rate_id(rate)}")
    return group


def choose_configuration(rows: dict[str, list[dict[str, Any]]], configs: list[dict[str, Any]]) -> str:
    keys = {item["id"] for item in configs}
    if set(rows) != keys:
        raise ValueError("selection candidates are incomplete")
    def score(key: str) -> tuple[int, int, str]:
        shots = rows[key]
        failures = sum(row["outcome"] not in VALID for row in shots)
        updates = sum(row["work_vector"]["check_to_variable_updates"] for row in shots)
        return failures, updates, key
    return min(keys, key=score)


def freeze_selection() -> dict[str, Any]:
    spec = design()
    seal = check_seal()
    configs = configurations(spec)
    rows: dict[str, list[dict[str, Any]]] = {item["id"]: [] for item in configs}
    identities_by_rate: dict[str, list[str]] = {}
    ledgers: dict[str, str] = {}
    for rate in spec["channel"]["x_error_rates"]:
        group = _verified_group(spec, "selection", rate, configs)
        rate_id = _rate_id(rate)
        identities_by_rate[rate_id] = [group[configs[0]["id"]][shot]["sample_identity"] for shot in range(spec["cohorts"]["selection"]["shots_per_rate"])]
        for config in configs:
            key = config["id"]
            rows[key].extend(group[key][shot] for shot in sorted(group[key]))
            ledgers[f"{rate_id}/{key}"] = _digest(_arm_path("selection", rate, config) / "events.jsonl")
    selected = {}
    for family in (item["id"] for item in spec["families"]):
        family_configs = [config for config in configs if config["family"] == family]
        selected[family] = choose_configuration({item["id"]: rows[item["id"]] for item in family_configs}, family_configs)
    lock = {
        "schema_version": 1, "study_id": spec["study_id"], "design_sha256": _digest(DESIGN),
        "seal_sha256": sha256(_bytes(seal)).hexdigest(), "selected_configuration_ids": selected,
        "selection_ledger_sha256": ledgers, "selection_sample_identities": identities_by_rate,
        "selection_rule": spec["selection_rule"],
    }
    _write_once(OUTPUT / "selection-lock.json", _bytes(lock))
    return lock


def selection_lock() -> dict[str, Any]:
    saved = _read(OUTPUT / "selection-lock.json")
    if saved != freeze_selection():
        raise ValueError("selection lock differs from verified selection ledgers")
    return saved


def _rate_interval(failures: int, shots: int, alpha: float = 0.05) -> tuple[float, float]:
    if not 0 <= failures <= shots or shots < 1:
        raise ValueError("invalid binomial count")
    lower = 0.0 if failures == 0 else float(beta.ppf(alpha / 2, failures, shots - failures + 1))
    upper = 1.0 if failures == shots else float(beta.ppf(1 - alpha / 2, failures + 1, shots - failures))
    return lower, upper


def _holm(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=lambda key: (p_values[key], key))
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for index, key in enumerate(ordered):
        running = max(running, min(1.0, (count - index) * p_values[key]))
        adjusted[key] = running
    return adjusted


def _summarize(rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    outcomes = Counter(row["outcome"] or "outcome_unavailable" for row in rows.values())
    terminations = Counter(row["termination"] for row in rows.values())
    failures = sum(count for outcome, count in outcomes.items() if outcome not in VALID)
    shots = len(rows)
    interval = _rate_interval(failures, shots)
    vector_names = sorted(next(iter(rows.values()))["work_vector"])
    runtime_values = [row["decode_runtime_ns"] for row in rows.values() if row["decode_runtime_ns"] is not None]
    convergence_values = [row["converged"] for row in rows.values() if row["converged"] is not None]
    return {
        "shots": shots, "failures": failures, "failure_rate": failures / shots,
        "failure_interval_95": list(interval),
        "failure_interval_halfwidth": (interval[1] - interval[0]) / 2,
        "outcomes": dict(sorted(outcomes.items())), "terminations": dict(sorted(terminations.items())),
        "mean_work_vector": {name: sum(row["work_vector"][name] for row in rows.values()) / shots for name in vector_names},
        "decode_runtime_ns": {
            "available_shots": len(runtime_values),
            "mean_when_available": sum(runtime_values) / len(runtime_values) if runtime_values else None,
            "qualification": "observed canonical decode timing, not normalized across controller versions" if runtime_values else "not_available_in_terminal_evidence",
        },
        "convergence": {
            "available_shots": len(convergence_values),
            "converged_when_available": sum(bool(value) for value in convergence_values) if convergence_values else None,
            "qualification": "not_available_in_terminal_evidence" if not convergence_values else "producer_reported",
        },
    }


def _contrast(reference: dict[int, dict[str, Any]], other: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if set(reference) != set(other) or any(reference[shot]["sample_identity"] != other[shot]["sample_identity"] for shot in reference):
        raise ValueError("paired contrast has mismatched physical samples")
    new_valid = sum(reference[shot]["outcome"] not in VALID and other[shot]["outcome"] in VALID for shot in reference)
    lost_valid = sum(reference[shot]["outcome"] in VALID and other[shot]["outcome"] not in VALID for shot in reference)
    discordant = new_valid + lost_valid
    exact_p = 1.0 if discordant == 0 else float(binomtest(new_valid, discordant, 0.5, alternative="two-sided").pvalue)
    return {
        "newly_valid": new_valid, "lost_valid": lost_valid, "discordant": discordant,
        "failure_rate_difference_vs_reference": (lost_valid - new_valid) / len(reference),
        "mcnemar_exact_two_sided_p": exact_p,
    }


def report() -> dict[str, Any]:
    spec = design()
    seal = check_seal()
    lock = selection_lock()
    arms = _evaluation_arms(spec, lock)
    configs = list(dict((config["id"], config) for _, _, config in arms).values())
    selected = lock["selected_configuration_ids"]
    summaries: dict[str, Any] = {}
    contrasts: dict[str, Any] = {}
    p_values: dict[str, float] = {}
    evaluation_samples: dict[str, list[str]] = {}
    evaluation_ledgers: dict[str, str] = {}
    for rate in spec["channel"]["x_error_rates"]:
        rate_id = _rate_id(rate)
        group = _verified_group(spec, "evaluation", rate, configs)
        reference = group["spa-g1000"]
        identities = [reference[shot]["sample_identity"] for shot in sorted(reference)]
        if set(identities).intersection(lock["selection_sample_identities"][rate_id]):
            raise ValueError("evaluation reused parameter-selection physical samples")
        evaluation_samples[rate_id] = identities
        summaries[rate_id] = {}
        for config in configs:
            key = config["id"]
            summaries[rate_id][key] = _summarize(group[key])
            if summaries[rate_id][key]["failure_interval_halfwidth"] > spec["assessment"]["marginal_rate_halfwidth_target"]:
                raise ValueError("evaluation rate precision target was not met")
            evaluation_ledgers[f"{rate_id}/{key}"] = _digest(_arm_path("evaluation", rate, config) / "events.jsonl")
        for family, key in selected.items():
            if key == "spa-g1000":
                continue
            comparison_id = f"{rate_id}/{family}"
            contrasts[comparison_id] = {"family": family, "configuration_id": key, **_contrast(reference, group[key])}
            p_values[comparison_id] = contrasts[comparison_id]["mcnemar_exact_two_sided_p"]
    adjusted = _holm(p_values)
    for key, row in contrasts.items():
        row["holm_adjusted_p"] = adjusted[key]
        row["assessment"] = (
            "lower_failure_than_reference" if row["holm_adjusted_p"] <= spec["assessment"]["alpha"] and row["failure_rate_difference_vs_reference"] < 0 else
            "higher_failure_than_reference" if row["holm_adjusted_p"] <= spec["assessment"]["alpha"] and row["failure_rate_difference_vs_reference"] > 0 else
            "inconclusive"
        )
    result = {
        "schema_version": 1, "study_id": spec["study_id"], "relation": "controlled_css_adaptation",
        "source_reproduction_assessment": "not_applicable", "design_sha256": _digest(DESIGN),
        "seal_sha256": sha256(_bytes(seal)).hexdigest(), "selection_lock_sha256": _digest(OUTPUT / "selection-lock.json"),
        "selected_configuration_ids": selected, "evaluation_sample_identities": evaluation_samples,
        "evaluation_ledger_sha256": evaluation_ledgers, "shared_work_view": {"summaries": summaries, "contrasts": contrasts},
        "source_settings_view": spec["source_settings_view"],
        "claim_limit": spec["claim_scope"],
    }
    _write_once(OUTPUT / "result.json", _bytes(result))
    lines = [
        "# BB72 CSS BP comparison v1", "",
        "Source-pinned [[72,12,6]] BB72 artifact; X-only code-capacity noise. Every evaluation denominator includes all terminal shots.",
        f"Selection: {spec['cohorts']['selection']['shots_per_rate']} matched samples per rate; evaluation: {spec['cohorts']['evaluation']['shots_per_rate']} new matched samples per rate.",
        f"Frozen design SHA-256: `{_digest(DESIGN)}`. All public arms replay-verified before this report.",
        "The common cap is 40 flooding BP sweeps or 8,640 messages in each direction per shot; non-message work and realized cost differ and are reported separately.",
        "", "## Selected configurations", "",
    ]
    lines.extend(f"- {family}: `{key}`" for family, key in selected.items())
    lines.extend(["", "## Shared-work view", "", "| p | Configuration | Failures / 512 | 95% exact interval | Mean C2V updates |", "| ---: | --- | ---: | --- | ---: |"])
    for rate in spec["channel"]["x_error_rates"]:
        rate_id = _rate_id(rate)
        for key, row in summaries[rate_id].items():
            low, high = row["failure_interval_95"]
            lines.append(f"| {rate:.2f} | `{key}` | {row['failures']} / {row['shots']} | [{low:.3f}, {high:.3f}] | {row['mean_work_vector']['check_to_variable_updates']:.1f} |")
    lines.extend(["", "## Paired comparisons with undamped SPA", "", "| p | Family | Newly valid | Lost valid | Failure difference | Holm p | Assessment |", "| ---: | --- | ---: | ---: | ---: | ---: | --- |"])
    for key, row in sorted(contrasts.items()):
        rate_id, family = key.split("/", 1)
        lines.append(f"| {int(rate_id[1:])/1000:.2f} | {family} | {row['newly_valid']} | {row['lost_valid']} | {row['failure_rate_difference_vs_reference']:+.3f} | {row['holm_adjusted_p']:.4g} | {row['assessment']} |")
    lines.extend(["", "## Source-settings view", "", "These records distinguish the source paper's original problem and settings from the BB72 CSS arms above. No row below is a source-curve reproduction.", "", "| Source configuration | BB72 CSS status | Reason |", "| --- | --- | --- |"])
    for row in spec["source_settings_view"]:
        lines.append(f"| {row['id']} | {row['bb72_css_status']} | {row['reason']} |")
    lines.extend(["", "The exact paper links, per-arm manifests, terminal ledgers, and uncertainty rules are in the frozen design and study output. A difference at one BB72 rate does not establish a decoder ranking across codes or channels.", ""])
    _write_once(OUTPUT / "REPORT.md", "\n".join(lines).encode())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight-selection", "run-selection", "freeze-selection", "preflight-evaluation", "run-evaluation", "report"))
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()
    if args.action == "preflight-selection":
        print(json.dumps({"status": "preflighted", "arms": len(prepare("selection")), "design_sha256": _digest(DESIGN)}))
    elif args.action == "run-selection":
        print(json.dumps({"status": "verified", "arms": len(run("selection", args.workers))}))
    elif args.action == "freeze-selection":
        print(json.dumps(freeze_selection()["selected_configuration_ids"], sort_keys=True))
    elif args.action == "preflight-evaluation":
        print(json.dumps({"status": "preflighted", "arms": len(prepare("evaluation")), "design_sha256": _digest(DESIGN)}))
    elif args.action == "run-evaluation":
        print(json.dumps({"status": "verified", "arms": len(run("evaluation", args.workers))}))
    else:
        result = report()
        print(json.dumps({"status": "reported", "arms": len(result["evaluation_ledger_sha256"]), "report": str(OUTPUT / "REPORT.md")}))


if __name__ == "__main__":
    main()
