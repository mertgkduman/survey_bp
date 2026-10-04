#!/usr/bin/env python3
"""Run the frozen, independent BB72 BP-SF kernel/damping factorial."""

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


DESIGN = ROOT / "data/studies/bb72-bpsf-factorial-v2.json"
BB72_BASE = ROOT / "data/manifests/phase3-pilot-bb72.json"
INTERVENTION_BASE = ROOT / "data/manifests/phase5-b1-mechanism-pilot.json"
OUTPUT = ROOT / "data/results/bb72-bpsf-factorial-v2"
CODE_FILES = tuple(sorted(str(path.relative_to(ROOT)) for path in (ROOT / "src/bp_registry").rglob("*.py"))) + (
    "data/manifests/phase3-pilot-bb72.json", "data/manifests/phase5-b1-mechanism-pilot.json",
    "scripts/run_bb72_bpsf_factorial_v2.py",
)
VALID = frozenset(("exact", "stabilizer_equivalent"))


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _write_once(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"sealed evidence differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _rate_id(rate: float) -> str:
    return f"p{int(round(rate * 1000)):03d}"


def design() -> dict[str, Any]:
    value = _read(DESIGN)
    if value.get("study_id") != "bb72-bpsf-factorial-v2" or value.get("status") != "prespecified_before_study_sampling":
        raise ValueError("unexpected factorial study design")
    if value["channel"]["x_error_rates"] != [0.05, 0.08] or value["cohort"]["shots_per_rate"] != {"p050": 512, "p080": 1280}:
        raise ValueError("frozen rates or shot counts differ")
    factorial = value["factorial"]
    if (factorial["update"] != ["binary_spa", "min_sum"] or factorial["damping_gamma"] != [1.0, 0.5]
            or factorial["mode"] != ["bp20", "bp40", "bpsf20plus4x5"] or factorial["arm_count_per_rate"] != 12):
        raise ValueError("frozen factorial differs")
    if value["assessment"]["primary_contrasts"] != [
        {"id": "spa-bpsf-vs-spa-bp40", "update": "binary_spa", "gamma": 1.0,
         "new_mode": "bpsf20plus4x5", "reference_mode": "bp40"},
        {"id": "ms-bpsf-vs-ms-bp40", "update": "min_sum", "gamma": 1.0,
         "new_mode": "bpsf20plus4x5", "reference_mode": "bp40"},
    ]:
        raise ValueError("primary contrast family differs")
    if _digest(ROOT / "data/artifacts/bb72-css.json") != value["artifact"]["raw_sha256"]:
        raise ValueError("source-pinned BB72 artifact differs")
    work = value["shared_work"]
    if (work["edge_count"] != 216 or work["max_bp_sweeps_per_shot"] != 40
            or work["max_check_to_variable_updates_per_shot"] != 8640
            or work["max_variable_to_check_updates_per_shot"] != 8640):
        raise ValueError("frozen work envelope differs")
    return value


def configurations(spec: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    spec = design() if spec is None else spec
    configs = []
    for update, gamma, mode in product(spec["factorial"]["update"], spec["factorial"]["damping_gamma"], spec["factorial"]["mode"]):
        label = "spa" if update == "binary_spa" else "ms"
        configs.append({"id": f"{label}-g{int(round(gamma * 1000)):04d}-{mode}",
                        "update": update, "gamma": gamma, "mode": mode})
    if len(configs) != 12 or len({row["id"] for row in configs}) != 12:
        raise ValueError("factorial arm identity differs")
    return configs


def _memory(gamma: float) -> dict[str, Any]:
    return {"bindings": [{
        "binding_id": "v2c-damping", "kind": "v2c_damping", "target": "v2c",
        "parameters": {"gamma": gamma}, "order": 0,
        "history_owner": "attempt:v2c-damping", "state_lifetime": "attempt",
        "advance_boundary": "source_iteration", "refresh_boundary": "attempt_start",
        "source_status": "canonical_adaptation", "retain_history": False,
    }]}


def make_manifest(spec: dict[str, Any], config: dict[str, Any], rate: float) -> dict[str, Any]:
    if config not in configurations(spec) or rate not in spec["channel"]["x_error_rates"]:
        raise ValueError("configuration is outside the frozen factorial")
    mode, update, gamma = config["mode"], config["update"], config["gamma"]
    if mode == "bpsf20plus4x5":
        manifest = deepcopy(_read(INTERVENTION_BASE)["arm_manifests"]["syndrome_flip"])
        manifest["schema_version"] = 6
        manifest["artifact"] = deepcopy(_read(BB72_BASE)["artifact"])
        for key, value in spec["factorial"]["bpsf_controls"].items():
            if key != "selection":
                manifest["intervention"][key] = value
        manifest["intervention"]["root_seed"] = f"{spec['study_id']}-{_rate_id(rate)}-decoder"
    else:
        manifest = deepcopy(_read(BB72_BASE))
        manifest["schema_version"] = 4
    manifest["memory"] = _memory(gamma)
    manifest["numerical_profile"] = "cpu-float64-spa-v1" if update == "binary_spa" else "cpu-float64-min-sum-v1"
    manifest["policies"]["update"].update({
        "kind": update,
        "binding_id": "update-binary-spa-v1" if update == "binary_spa" else "update-min-sum-v1",
    })
    sweeps = 20 if mode == "bp20" else 40
    for scope in ("shot", "search", "attempt"):
        limits = manifest["budgets"][scope]
        limits["max_iterations"] = sweeps
        limits["work_limits"].update({
            "check_to_variable_updates": 8640, "variable_to_check_updates": 8640,
            "belief_assemblies": 8640, "candidate_checks": 8640, "bp_calls": 32,
        })
    if mode == "bpsf20plus4x5":
        manifest["intervention_limits"]["work_caps"].update(manifest["budgets"]["attempt"]["work_limits"])
        manifest["intervention_limits"]["max_runtime_seconds"] = 300.0
    rate_id = _rate_id(rate)
    manifest["budgets"]["max_shots"] = spec["cohort"]["shots_per_rate"][rate_id]
    manifest["run_id"] = f"{spec['study_id']}-{rate_id}-{config['id']}"
    manifest["error_rate"] = rate
    manifest["randomness"].update({
        "sample_seed": spec["cohort"]["sample_seed"],
        "physical_sample_identity": f"{spec['cohort']['physical_sample_identity_prefix']}-{rate_id}",
        "decoder_seed_identity": f"{spec['study_id']}-{rate_id}-decoder",
    })
    manifest["evidence"] = {
        "relation": "canonical_implemented", "fixture": "development_fixture", "assessment_status": "not_assessed",
        "procedure": f"Prespecified BB72 BP-SF factorial; {rate_id}; {config['id']}; design sha256:{_digest(DESIGN)}",
        "sources": ["Bravyi et al. arXiv:2308.07915", "BP-SF arXiv:2507.00254v1",
                    "Gokduman et al. arXiv:2411.08177v2 Eq. 17"],
        "discrepancies": ["This X-only CSS study does not reproduce circuit-level BB72 BP-OSD.",
                          "Deterministic serial BP-SF is a controlled adaptation of source parallel selection."],
    }
    resolved = preflight(manifest).manifest
    if resolved.artifact.code_id != "bravyi-bb-72" or resolved.budgets.max_shots != spec["cohort"]["shots_per_rate"][rate_id]:
        raise ValueError("public preflight changed code or denominator")
    return manifest


def _seal() -> dict[str, Any]:
    return {"schema_version": 1, "study_id": "bb72-bpsf-factorial-v2",
            "design_sha256": _digest(DESIGN),
            "implementation_sha256": {name: _digest(ROOT / name) for name in CODE_FILES}}


def check_seal() -> dict[str, Any]:
    expected = _seal()
    target = OUTPUT / "seal.json"
    if not target.exists() and OUTPUT.exists() and any(OUTPUT.rglob("events.jsonl")):
        raise ValueError("study evidence exists without its presampling seal")
    _write_once(target, _bytes(expected))
    return expected


def arms(spec: dict[str, Any] | None = None) -> list[tuple[float, dict[str, Any]]]:
    spec = design() if spec is None else spec
    return [(rate, config) for rate in spec["channel"]["x_error_rates"] for config in configurations(spec)]


def _arm_path(rate: float, config: dict[str, Any]) -> Path:
    return OUTPUT / _rate_id(rate) / config["id"]


def prepare() -> list[tuple[Path, Path]]:
    spec = design()
    check_seal()
    paths = []
    for rate, config in arms(spec):
        root = _arm_path(rate, config)
        path = root / "manifest.json"
        _write_once(path, _bytes(make_manifest(spec, config, rate)))
        paths.append((path, root))
    return paths


def _execute(paths: tuple[Path, Path]) -> str:
    path, root = paths
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise ValueError("study requires OMP_NUM_THREADS=1 per worker")
    run_canonical(path, root)
    verified = verify_run(root)
    if verified["final_row_count"] != _read(path)["budgets"]["max_shots"]:
        raise ValueError(f"arm did not reach its fixed denominator: {root}")
    print(f"verified {root.relative_to(OUTPUT)}", flush=True)
    return str(root)


def run(workers: int | None = None) -> list[str]:
    paths = prepare()
    count = min(len(paths), workers or int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1)))
    if count < 1:
        raise ValueError("worker count must be positive")
    with ProcessPoolExecutor(max_workers=count) as pool:
        return list(pool.map(_execute, paths))


def _terminals(root: Path) -> dict[int, dict[str, Any]]:
    result = verify_run(root)
    manifest = _read(root / "manifest.json")
    if result["final_row_count"] != manifest["budgets"]["max_shots"]:
        raise ValueError(f"incomplete arm: {root}")
    starts: dict[int, str] = {}
    finals: dict[int, dict[str, Any]] = {}
    for event in read_canonical_events(root / "events.jsonl"):
        shot_id = event["shot_id"]
        if event["kind"] == "shot_begin":
            if shot_id in starts:
                raise ValueError("duplicate shot beginning")
            starts[shot_id] = event["sample_seed_identity"]
        elif event["kind"] == "termination":
            if shot_id in finals:
                raise ValueError("duplicate shot terminal")
            data = event["data"]
            payload = data.get("payload", data)
            runtime = payload.get("decode_runtime")
            if (not isinstance(runtime, dict) or type(runtime.get("value")) is not int
                    or runtime["value"] < 0):
                raise ValueError(f"missing observed intervention/BP runtime: {root}/{shot_id}")
            finals[shot_id] = {
                "outcome": payload.get("outcome"), "termination": event["termination"],
                "work_vector": payload["work_vector"], "decode_runtime": runtime,
            }
    expected = set(range(manifest["budgets"]["max_shots"]))
    if set(starts) != expected or set(finals) != expected:
        raise ValueError(f"missing physical or terminal shots: {root}")
    for shot_id in finals:
        finals[shot_id]["sample_identity"] = starts[shot_id]
    return finals


def _rate_group(rate: float, configs: list[dict[str, Any]]) -> dict[str, dict[int, dict[str, Any]]]:
    requested = int(os.environ.get("BB72_V2_VERIFY_WORKERS", os.environ.get("SLURM_CPUS_PER_TASK", "8")))
    if requested < 1:
        raise ValueError("BB72_V2_VERIFY_WORKERS must be positive")
    with ProcessPoolExecutor(max_workers=min(len(configs), requested)) as pool:
        sets = list(pool.map(_terminals, [_arm_path(rate, config) for config in configs]))
    group = {config["id"]: rows for config, rows in zip(configs, sets, strict=True)}
    first = next(iter(group.values()))
    identities = tuple(first[shot]["sample_identity"] for shot in sorted(first))
    for rows in group.values():
        if tuple(rows[shot]["sample_identity"] for shot in sorted(rows)) != identities:
            raise ValueError(f"unmatched physical sample identities: {_rate_id(rate)}")
    return group


def _interval(failures: int, shots: int) -> list[float]:
    return [0.0 if failures == 0 else float(beta.ppf(.025, failures, shots - failures + 1)),
            1.0 if failures == shots else float(beta.ppf(.975, failures + 1, shots - failures))]


def _summary(rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    shots = len(rows)
    outcomes = Counter(row["outcome"] or "unavailable" for row in rows.values())
    failures = sum(count for name, count in outcomes.items() if name not in VALID)
    work_keys = set(next(iter(rows.values()))["work_vector"])
    if any(set(row["work_vector"]) != work_keys for row in rows.values()):
        raise ValueError("work vector field set varies within one arm")
    methods = {row["decode_runtime"]["method"] for row in rows.values()}
    scopes = {row["decode_runtime"]["scope"] for row in rows.values()}
    if len(methods) != 1 or len(scopes) != 1:
        raise ValueError("runtime method or scope varies within one arm")
    return {"shots": shots, "failures": failures, "failure_rate": failures / shots,
            "failure_interval_95": _interval(failures, shots),
            "outcomes": dict(sorted(outcomes.items())),
            "terminations": dict(sorted(Counter(row["termination"] for row in rows.values()).items())),
            "mean_work_vector": {key: sum(row["work_vector"][key] for row in rows.values()) / shots for key in sorted(work_keys)},
            "runtime": {"available_shots": shots, "method": methods.pop(), "scope": scopes.pop(),
                        "mean_ns": sum(row["decode_runtime"]["value"] for row in rows.values()) / shots}}


def _contrast(reference: dict[int, dict[str, Any]], other: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if set(reference) != set(other) or any(reference[i]["sample_identity"] != other[i]["sample_identity"] for i in reference):
        raise ValueError("paired contrast is unmatched")
    gained = sum(reference[i]["outcome"] not in VALID and other[i]["outcome"] in VALID for i in reference)
    lost = sum(reference[i]["outcome"] in VALID and other[i]["outcome"] not in VALID for i in reference)
    return {"newly_valid": gained, "lost_valid": lost,
            "failure_rate_difference": (lost - gained) / len(reference),
            "mcnemar_exact_two_sided_p": (1.0 if gained + lost == 0 else
                                          float(binomtest(gained, gained + lost, .5).pvalue))}


def _holm(values: dict[str, float]) -> dict[str, float]:
    adjusted: dict[str, float] = {}
    running = 0.0
    for index, key in enumerate(sorted(values, key=lambda key: (values[key], key))):
        running = max(running, min(1.0, (len(values) - index) * values[key]))
        adjusted[key] = running
    return adjusted


def report() -> dict[str, Any]:
    spec = design()
    seal = check_seal()
    configs = configurations(spec)
    summaries: dict[str, Any] = {}
    primary: dict[str, Any] = {}
    secondary: dict[str, Any] = {}
    identities: dict[str, list[str]] = {}
    ledgers: dict[str, str] = {}
    primary_ids = {item["update"]: item["id"] for item in spec["assessment"]["primary_contrasts"]}
    v1_root = ROOT / "data/results/bb72-css-bp-v1"
    v1_package = _read(v1_root / "publication-manifest.json")
    if _digest(v1_root / "result.json") != v1_package["result_sha256"]:
        raise ValueError("published v1 result differs from its package manifest")
    v1_samples = _read(v1_root / "result.json")["evaluation_sample_identities"]
    for rate in spec["channel"]["x_error_rates"]:
        rate_id = _rate_id(rate)
        group = _rate_group(rate, configs)
        first = group[configs[0]["id"]]
        identities[rate_id] = [first[i]["sample_identity"] for i in sorted(first)]
        if set(identities[rate_id]).intersection(v1_samples[rate_id]):
            raise ValueError(f"v2 reused a v1 physical sample identity: {rate_id}")
        summaries[rate_id] = {}
        for config in configs:
            key = config["id"]
            summaries[rate_id][key] = _summary(group[key])
            ledgers[f"{rate_id}/{key}"] = _digest(_arm_path(rate, config) / "events.jsonl")
        for update, gamma in product(spec["factorial"]["update"], spec["factorial"]["damping_gamma"]):
            label = "spa" if update == "binary_spa" else "ms"
            prefix = f"{label}-g{int(round(gamma * 1000)):04d}"
            for mode in ("bp20", "bpsf20plus4x5"):
                key = f"{rate_id}/{prefix}/{mode}-vs-bp40"
                contrast = _contrast(group[f"{prefix}-bp40"], group[f"{prefix}-{mode}"])
                if rate_id == "p080" and gamma == 1.0 and mode == "bpsf20plus4x5":
                    primary[primary_ids[update]] = contrast
                else:
                    secondary[key] = {name: value for name, value in contrast.items() if name != "mcnemar_exact_two_sided_p"}
    if len(primary) != 2:
        raise ValueError("primary contrast family differs from frozen design")
    adjusted = _holm({key: row["mcnemar_exact_two_sided_p"] for key, row in primary.items()})
    for key, row in primary.items():
        row["holm_adjusted_p"] = adjusted[key]
        row["assessment"] = (
            "lower_failure_than_reference" if adjusted[key] <= .05 and row["failure_rate_difference"] < 0 else
            "higher_failure_than_reference" if adjusted[key] <= .05 and row["failure_rate_difference"] > 0 else
            "inconclusive"
        )
    result = {"schema_version": 1, "study_id": spec["study_id"], "relation": "controlled_css_adaptation",
              "source_reproduction_assessment": "not_applicable", "design_sha256": _digest(DESIGN),
              "seal_sha256": sha256(_bytes(seal)).hexdigest(), "evaluation_sample_identities": identities,
              "evaluation_ledger_sha256": ledgers, "summaries": summaries,
              "primary_contrasts": primary, "secondary_descriptive_contrasts": secondary,
              "source_settings_view": spec["source_settings_view"], "claim_limit": spec["claim_scope"]}
    _write_once(OUTPUT / "result.json", _bytes(result))
    lines = ["# BB72 BP-SF factorial v2", "", spec["claim_scope"],
             "Independent fixed-shot cohort; no v1 shots pooled. All terminal outcomes remain in the denominator.",
             f"Design SHA-256: `{_digest(DESIGN)}`. All 24 arms passed public replay verification.",
             "", "## Failure and cost view", "",
             "| p | Arm | Failures / shots | 95% exact interval | Mean C2V | Mean BP calls | Mean measured runtime (ms) |",
             "| ---: | --- | ---: | --- | ---: | ---: | ---: |"]
    for rate in spec["channel"]["x_error_rates"]:
        rate_id = _rate_id(rate)
        for key, row in summaries[rate_id].items():
            low, high = row["failure_interval_95"]
            lines.append(f"| {rate:.2f} | `{key}` | {row['failures']} / {row['shots']} | [{low:.3f}, {high:.3f}] | {row['mean_work_vector']['check_to_variable_updates']:.1f} | {row['mean_work_vector']['bp_calls']:.2f} | {row['runtime']['mean_ns']/1e6:.1f} |")
    lines.extend(["", "Runtime methods and scopes differ between BP-only and BP-SF arms; these are same-node serial observations, not source parallel latency. Full typed work vectors and runtime metadata are in `result.json`.",
                  "", "## Prespecified primary paired contrasts at p=0.08", "",
                  "| Contrast | Newly valid | Lost valid | Failure difference | Holm p | Assessment |",
                  "| --- | ---: | ---: | ---: | ---: | --- |"])
    for key, row in sorted(primary.items()):
        lines.append(f"| `{key}` | {row['newly_valid']} | {row['lost_valid']} | {row['failure_rate_difference']:+.3f} | {row['holm_adjusted_p']:.4g} | {row['assessment']} |")
    lines.extend(["", "All other contrasts are descriptive and appear in `result.json`; no unadjusted directional claim is made for them.",
                  "", "## Source status", "", "| Variant | Status | Reason |", "| --- | --- | --- |"])
    for item in spec["source_settings_view"]:
        lines.append(f"| {item['id']} | {item['status']} | {item['reason']} |")
    _write_once(OUTPUT / "REPORT.md", ("\n".join(lines) + "\n").encode())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "run", "report"))
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()
    if args.action == "preflight":
        print(json.dumps({"status": "preflighted", "arms": len(prepare()), "design_sha256": _digest(DESIGN)}))
    elif args.action == "run":
        print(json.dumps({"status": "verified", "arms": len(run(args.workers))}))
    else:
        print(json.dumps({"status": "reported", "arms": len(report()["evaluation_ledger_sha256"])}))


if __name__ == "__main__":
    main()
