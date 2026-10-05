#!/usr/bin/env python3
"""Prespecified, matched BB72 CSS BeamSearch/RelayBP parameter campaign."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from hashlib import sha256
from html import escape
from importlib.metadata import version
from itertools import repeat
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np
from scipy.stats import beta, binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from bp_registry.artifacts import load_artifact  # noqa: E402
from bp_registry.canonical.fair_legs import FairLegConfig  # noqa: E402
from run_fair_beam_relay_css import _bytes, _deterministic, _rows, _shot  # noqa: E402


VALID = frozenset(("exact", "stabilizer_equivalent"))
MODES = ("beam", "relay")
GAMMAS = ("g1000", "g0500")
SOURCE_FILES = tuple(sorted(str(path.relative_to(ROOT)) for path in (ROOT / "src/bp_registry").rglob("*.py"))) + (
    "scripts/run_fair_beam_relay_css.py", "scripts/run_fair_beam_relay_campaign.py",
)


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_once(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"frozen file differs: {path}")
        return
    path.write_bytes(payload)


def _design(path: Path) -> dict:
    value = _read(path)
    if (value.get("schema_version") != 1 or value.get("study_id") != "fair-beam-relay-css-v2"
            or value.get("status") != "prespecified_before_sampling"
            or value.get("source_status") != "controlled_css_adaptation"
            or value.get("damping_gammas") != [1.0, 0.5]
            or set(value.get("rates", {})) != {"p050", "p080"}
            or set(value.get("cohorts", {})) != {"selection", "evaluation"}
            or set(value.get("profiles", {})) != {"i05", "i10", "i20"}):
        raise ValueError("unexpected campaign design or missing frozen controls")
    if any(type(value["rates"][rate][f"{cohort}_shots"]) is not int
           or value["rates"][rate][f"{cohort}_shots"] < 1
           for rate in value["rates"] for cohort in value["cohorts"]):
        raise ValueError("every cohort must have a fixed positive denominator")
    if value["rates"]["p050"]["error_rate"] != 0.05 or value["rates"]["p080"]["error_rate"] != 0.08:
        raise ValueError("rate labels must retain their prespecified noise levels")
    if (any(type(group.get("sample_seed")) is not int or group["sample_seed"] < 0
            or not isinstance(group.get("physical_identity_prefix"), str)
            or not group["physical_identity_prefix"] for group in value["cohorts"].values())
            or len({(group["sample_seed"], group["physical_identity_prefix"])
                    for group in value["cohorts"].values()}) != 2):
        raise ValueError("selection and evaluation sample namespaces must be distinct")
    if sorted(value["profiles"][key]["extra_iterations_per_unit"] for key in value["profiles"]) != [5, 10, 20]:
        raise ValueError("campaign profile grid differs from prespecified controls")
    controls = value["common_controls"]
    if (controls["initial_iterations"] != 20 or controls["max_extra_c2v_updates"] != 8640
            or controls["max_extra_units"] != 8 or controls["beam_width"] != 2
            or controls["beam_rounds"] != 4 or controls["solution_limit"] != 1):
        raise ValueError("shared work and topology controls differ from prespecification")
    for profile in value["profiles"].values():
        FairLegConfig(**controls, **profile, v2c_gamma=0.5)
    load_artifact(ROOT, value["artifact_path"],
                  expected_raw_sha256=value["artifact_raw_sha256"],
                  expected_semantic_sha256=value["artifact_semantic_sha256"])
    return value


def _seal(design_path: Path) -> dict:
    return {
        "schema_version": 1,
        "study_id": "fair-beam-relay-css-v2",
        "design_sha256": _digest(design_path),
        "artifact_raw_sha256": _read(design_path)["artifact_raw_sha256"],
        "source_sha256": {name: _digest(ROOT / name) for name in SOURCE_FILES},
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "scipy": version("scipy")},
    }


def prepare(design_path: Path, output: Path) -> dict:
    _design(design_path)
    frozen = output / "design.json"
    _write_once(frozen, design_path.read_bytes())
    seal = _seal(frozen)
    _write_once(output / "seal.json", json.dumps(seal, indent=2, sort_keys=True).encode() + b"\n")
    return seal


def _checked(design_path: Path, output: Path) -> dict:
    frozen = output / "design.json"
    if not frozen.is_file() or frozen.read_bytes() != design_path.read_bytes():
        raise ValueError("campaign design is not frozen or differs")
    design = _design(frozen)
    if _read(output / "seal.json") != _seal(frozen):
        raise ValueError("campaign source seal differs")
    return design


def _shard_path(output: Path, cohort: str, rate: str, profile: str) -> Path:
    return output / cohort / rate / profile


def _spec(design: dict, cohort: str, rate: str, profile: str) -> tuple[dict, FairLegConfig]:
    if cohort not in design["cohorts"] or rate not in design["rates"] or profile not in design["profiles"]:
        raise ValueError("unknown campaign shard")
    group = design["cohorts"][cohort]
    setting = design["rates"][rate]
    spec = {
        "study_id": f"{design['study_id']}-{cohort}-{rate}-{profile}",
        "sample_seed": group["sample_seed"],
        "physical_sample_identity": f"{group['physical_identity_prefix']}-{rate}",
        "error_rate": setting["error_rate"],
        "damping_gammas": design["damping_gammas"],
        "shots": setting[f"{cohort}_shots"],
    }
    controls = FairLegConfig(**design["common_controls"], **design["profiles"][profile], v2c_gamma=0.5)
    return spec, controls


def _manifest(design: dict, output: Path, cohort: str, rate: str, profile: str) -> dict:
    spec, controls = _spec(design, cohort, rate, profile)
    lock = output / "selection-lock.json"
    if cohort == "evaluation" and not lock.is_file():
        raise ValueError("evaluation requires a frozen parameter-selection lock")
    return {
        "schema_version": 1, "study_id": design["study_id"], "cohort": cohort,
        "rate": rate, "profile": profile, "spec": spec, "controls": asdict(controls),
        "design_sha256": _digest(output / "design.json"),
        "seal_sha256": _digest(output / "seal.json"),
        "selection_lock_sha256": _digest(lock) if cohort == "evaluation" else None,
        "source_status": "controlled_css_adaptation", "assessment_status": "not_assessed",
    }


def _shard_result(root: Path, manifest: dict, rows: list[dict]) -> dict:
    return {
        "schema_version": 1, "study_id": manifest["study_id"], "cohort": manifest["cohort"],
        "rate": manifest["rate"], "profile": manifest["profile"],
        "manifest_sha256": _digest(root / "manifest.json"),
        "ledger_sha256": _digest(root / "events.jsonl"), "shots": len(rows),
        "selection_lock_sha256": manifest["selection_lock_sha256"],
        "outcomes": {gamma: {mode: dict(Counter(row["arms"][gamma]["outcomes"][mode] for row in rows))
                             for mode in ("initial", *MODES)} for gamma in GAMMAS},
        "source_status": "controlled_css_adaptation", "assessment_status": "not_assessed",
    }


def _compute_shot(args: tuple[dict, FairLegConfig, object, int]) -> dict:
    return _shot(*args)


def _computed_shots(spec: dict, controls: FairLegConfig, code: object, *, workers: int):
    if workers == 1:
        for shot_id in range(spec["shots"]):
            yield _shot(spec, controls, code, shot_id)
    else:
        arguments = zip(repeat(spec), repeat(controls), repeat(code), range(spec["shots"]))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            yield from pool.map(_compute_shot, arguments, chunksize=1)


def run_shard(design_path: Path, output: Path, cohort: str, rate: str, profile: str,
              *, verify: bool = False, workers: int = 1) -> dict:
    if type(workers) is not int or workers < 1:
        raise ValueError("shot worker count must be positive")
    design = _checked(design_path, output)
    spec, controls = _spec(design, cohort, rate, profile)
    root = _shard_path(output, cohort, rate, profile)
    manifest = _manifest(design, output, cohort, rate, profile)
    frozen_manifest = root / "manifest.json"
    if verify and not frozen_manifest.is_file():
        raise ValueError("shard manifest is missing")
    _write_once(frozen_manifest, json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n")
    code = load_artifact(ROOT, design["artifact_path"],
                         expected_raw_sha256=design["artifact_raw_sha256"],
                         expected_semantic_sha256=design["artifact_semantic_sha256"]).code
    ledger = root / "events.jsonl"
    rows = _rows(ledger)
    if [row.get("shot_id") for row in rows] != list(range(len(rows))) or len(rows) > spec["shots"]:
        raise ValueError("shard has duplicate, reordered, or out-of-range shots")
    if verify and len(rows) != spec["shots"]:
        raise ValueError("shard denominator is incomplete")
    for shot_id, expected in enumerate(_computed_shots(spec, controls, code, workers=workers)):
        if shot_id < len(rows):
            if _deterministic(rows[shot_id]) != _deterministic(expected):
                raise ValueError(f"deterministic replay differs at {cohort}/{rate}/{profile}/{shot_id}")
        elif not verify:
            with ledger.open("ab") as handle:
                handle.write(_bytes(expected))
                handle.flush()
                os.fsync(handle.fileno())
            rows.append(expected)
    if len(rows) != spec["shots"]:
        raise ValueError("shard denominator is incomplete")
    result = _shard_result(root, manifest, rows)
    result_path = root / "result.json"
    if verify and not result_path.exists():
        raise ValueError("shard result is missing")
    _write_once(result_path, json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
    return result


def _verified_shard(args: tuple[Path, Path, str, str, str]) -> dict:
    return run_shard(*args, verify=True)


def _verify_group(design_path: Path, output: Path, cohort: str, *, workers: int) -> None:
    design = _checked(design_path, output)
    tasks = [(design_path, output, cohort, rate, profile)
             for rate in design["rates"] for profile in design["profiles"]]
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as pool:
        list(pool.map(_verified_shard, tasks))


def _group_rows(design: dict, output: Path, cohort: str, rate: str) -> dict[str, list[dict]]:
    profiles = {profile: _rows(_shard_path(output, cohort, rate, profile) / "events.jsonl")
                for profile in design["profiles"]}
    reference = next(iter(profiles.values()))
    if len(reference) != design["rates"][rate][f"{cohort}_shots"]:
        raise ValueError("group denominator differs")
    for rows in profiles.values():
        if len(rows) != len(reference):
            raise ValueError("profiles do not share a denominator")
        for first, row in zip(reference, rows, strict=True):
            if (first["shot_id"] != row["shot_id"] or first["sample_identity"] != row["sample_identity"]
                    or first["syndrome"] != row["syndrome"]):
                raise ValueError("profiles do not share physical samples")
            for gamma in GAMMAS:
                if first["arms"][gamma]["initial"] != row["arms"][gamma]["initial"]:
                    raise ValueError("profiles do not share initial BP semantics")
    return profiles


def _failures(rows: list[dict], gamma: str, mode: str) -> int:
    return sum(row["arms"][gamma]["outcomes"][mode] not in VALID for row in rows)


def _c2v(rows: list[dict], gamma: str, mode: str) -> int:
    return sum(row["arms"][gamma][mode]["total_work"]["check_to_variable_updates"] for row in rows)


def select(design_path: Path, output: Path, *, workers: int = 6) -> dict:
    design = _checked(design_path, output)
    if (output / "evaluation").exists():
        raise ValueError("selection lock must precede evaluation files")
    _verify_group(design_path, output, "selection", workers=workers)
    selected = {}
    source_hashes = {}
    for rate in design["rates"]:
        groups = _group_rows(design, output, "selection", rate)
        selected[rate] = {}
        for gamma in GAMMAS:
            selected[rate][gamma] = {}
            for mode in MODES:
                profile = min(groups, key=lambda key: (_failures(groups[key], gamma, mode),
                                                       _c2v(groups[key], gamma, mode), key))
                selected[rate][gamma][mode] = profile
        source_hashes[rate] = {profile: _digest(_shard_path(output, "selection", rate, profile) / "events.jsonl")
                               for profile in groups}
    lock = {
        "schema_version": 1, "study_id": design["study_id"],
        "design_sha256": _digest(output / "design.json"), "seal_sha256": _digest(output / "seal.json"),
        "rule": design["selection_rule"], "selection_ledger_sha256": source_hashes,
        "selected_profiles": selected,
    }
    _write_once(output / "selection-lock.json", json.dumps(lock, indent=2, sort_keys=True).encode() + b"\n")
    return lock


def _interval(failures: int, shots: int) -> tuple[float, float]:
    return (0.0 if failures == 0 else float(beta.ppf(0.025, failures, shots - failures + 1)),
            1.0 if failures == shots else float(beta.ppf(0.975, failures + 1, shots - failures)))


def _paired(beam: list[dict], relay: list[dict], gamma: str) -> dict:
    b = [row["arms"][gamma]["outcomes"]["beam"] in VALID for row in beam]
    r = [row["arms"][gamma]["outcomes"]["relay"] in VALID for row in relay]
    if len(b) != len(r):
        raise ValueError("paired comparison lacks matched denominator")
    beam_only = sum(x and not y for x, y in zip(b, r, strict=True))
    relay_only = sum(y and not x for x, y in zip(b, r, strict=True))
    discordant = beam_only + relay_only
    return {
        "beam_only_valid": beam_only, "relay_only_valid": relay_only,
        "discordant": discordant,
        "beam_minus_relay_failure": (relay_only - beam_only) / len(b),
        "raw_p": float(binomtest(beam_only, discordant, 0.5).pvalue) if discordant else 1.0,
    }


def _holm(contrasts: dict[str, dict]) -> None:
    ordered = sorted(contrasts, key=lambda key: (contrasts[key]["raw_p"], key))
    running = 0.0
    for position, key in enumerate(ordered):
        running = max(running, min(1.0, contrasts[key]["raw_p"] * (len(ordered) - position)))
        contrasts[key]["holm_p"] = running
        contrasts[key]["assessment"] = (
            "beam_lower_failure" if running <= 0.05 and contrasts[key]["beam_minus_relay_failure"] < 0 else
            "relay_lower_failure" if running <= 0.05 and contrasts[key]["beam_minus_relay_failure"] > 0 else
            "inconclusive"
        )


def _html_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    head = "<tr>" + "".join(f"<th>{escape(value)}</th>" for value in headers) + "</tr>"
    body = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>" for row in rows)
    return f"<table>{head}{body}</table>"


def report(design_path: Path, output: Path, *, workers: int = 6) -> dict:
    design = _checked(design_path, output)
    lock_path = output / "selection-lock.json"
    if not lock_path.is_file():
        raise ValueError("evaluation report requires a frozen selection lock")
    lock = _read(lock_path)
    if lock["design_sha256"] != _digest(output / "design.json") or lock["seal_sha256"] != _digest(output / "seal.json"):
        raise ValueError("selection lock differs from frozen design or source")
    if lock.get("rule") != design["selection_rule"] or set(lock.get("selection_ledger_sha256", {})) != set(design["rates"]):
        raise ValueError("selection lock rule or rate set differs")
    # Selection recheck is confined to its own cohort; selected settings were
    # frozen before evaluation shards could be created.
    for rate, profiles in lock["selection_ledger_sha256"].items():
        if set(profiles) != set(design["profiles"]):
            raise ValueError("selection lock profile set differs")
        for profile, digest in profiles.items():
            if _digest(_shard_path(output, "selection", rate, profile) / "events.jsonl") != digest:
                raise ValueError("selection evidence changed after locking")
    recomputed_selection = {}
    for rate in design["rates"]:
        groups = _group_rows(design, output, "selection", rate)
        recomputed_selection[rate] = {}
        for gamma in GAMMAS:
            recomputed_selection[rate][gamma] = {}
            for mode in MODES:
                recomputed_selection[rate][gamma][mode] = min(
                    groups, key=lambda key: (_failures(groups[key], gamma, mode),
                                             _c2v(groups[key], gamma, mode), key)
                )
    if lock.get("selected_profiles") != recomputed_selection:
        raise ValueError("selection lock does not match its prespecified rule")
    _verify_group(design_path, output, "evaluation", workers=workers)
    summaries = {}
    parameter_grid = {}
    initial_baselines = {}
    contrasts = {}
    evaluation_hashes = {}
    for rate in design["rates"]:
        groups = _group_rows(design, output, "evaluation", rate)
        evaluation_hashes[rate] = {profile: _digest(_shard_path(output, "evaluation", rate, profile) / "events.jsonl")
                                   for profile in groups}
        summaries[rate] = {}
        parameter_grid[rate] = {}
        initial_baselines[rate] = {}
        for gamma in GAMMAS:
            summaries[rate][gamma] = {}
            parameter_grid[rate][gamma] = {}
            baseline = next(iter(groups.values()))
            initial_failures = _failures(baseline, gamma, "initial")
            initial_baselines[rate][gamma] = {
                "failures": initial_failures, "shots": len(baseline),
                "failure_interval_95": list(_interval(initial_failures, len(baseline))),
                "mean_c2v": sum(row["arms"][gamma]["initial"]["work"]["check_to_variable_updates"]
                                for row in baseline) / len(baseline),
                "mean_runtime_ms": sum(row["arms"][gamma]["runtime_ns"]["initial"] for row in baseline)
                                   / len(baseline) / 1e6,
            }
            for profile, rows in groups.items():
                parameter_grid[rate][gamma][profile] = {}
                for mode in MODES:
                    failures = _failures(rows, gamma, mode)
                    runtime = sum(row["arms"][gamma]["runtime_ns"]["initial"]
                                  + row["arms"][gamma]["runtime_ns"][f"{mode}_extra"] for row in rows)
                    parameter_grid[rate][gamma][profile][mode] = {
                        "failures": failures, "shots": len(rows),
                        "failure_interval_95": list(_interval(failures, len(rows))),
                        "mean_initial_c2v": sum(row["arms"][gamma][mode]["initial_work"]["check_to_variable_updates"]
                                                for row in rows) / len(rows),
                        "mean_extra_c2v": sum(row["arms"][gamma][mode]["extra_work"]["check_to_variable_updates"]
                                              for row in rows) / len(rows),
                        "mean_total_c2v": _c2v(rows, gamma, mode) / len(rows),
                        "mean_runtime_ms": runtime / len(rows) / 1e6,
                    }
            for mode in MODES:
                profile = lock["selected_profiles"][rate][gamma][mode]
                summaries[rate][gamma][mode] = {"selected_profile": profile,
                                                 **parameter_grid[rate][gamma][profile][mode]}
            beam_rows = groups[lock["selected_profiles"][rate][gamma]["beam"]]
            relay_rows = groups[lock["selected_profiles"][rate][gamma]["relay"]]
            contrasts[f"{rate}/{gamma}"] = _paired(beam_rows, relay_rows, gamma)
    _holm(contrasts)
    result = {
        "schema_version": 1, "study_id": design["study_id"], "assessment_status": "controlled_evaluation_complete",
        "source_status": "controlled_css_adaptation", "design_sha256": _digest(output / "design.json"),
        "seal_sha256": _digest(output / "seal.json"), "selection_lock_sha256": _digest(lock_path),
        "evaluation_ledger_sha256": evaluation_hashes,
        "initial_baselines": initial_baselines, "parameter_grid": parameter_grid,
        "selected_summaries": summaries, "selected_paired_contrasts": contrasts,
        "claim_limit": "BB72 X-only CSS controlled comparison; no circuit-paper reproduction or cross-code ranking",
    }
    _write_once(output / "result.json", json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
    lines = ["# BB72 CSS BeamSearch versus RelayBP: matched parameter study", "",
             "This is a controlled X-only CSS adaptation, not either paper's circuit-level reproduction. ",
             "Selection and evaluation use disjoint physical sample identities. All terminal shots count.", "",
             f"Design SHA-256: `{result['design_sha256']}`. Selection lock SHA-256: `{result['selection_lock_sha256']}`.", "",
             "## Selected settings, failures, and cost", "",
             "| p | damping gamma | method | extra iterations/unit | failures/shots | 95% exact interval | mean total C2V | mean runtime ms |",
             "| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |"]
    for rate in design["rates"]:
        for gamma in GAMMAS:
            for mode in MODES:
                row = summaries[rate][gamma][mode]
                iteration = design["profiles"][row["selected_profile"]]["extra_iterations_per_unit"]
                low, high = row["failure_interval_95"]
                lines.append(f"| {design['rates'][rate]['error_rate']:.2f} | {float(gamma[1:])/1000:.1f} | {mode} | {iteration} | "
                             f"{row['failures']}/{row['shots']} | [{low:.3f}, {high:.3f}] | "
                             f"{row['mean_total_c2v']:.1f} | {row['mean_runtime_ms']:.1f} |")
    lines.extend(["", "## Prespecified paired contrasts", "",
                  "| p / gamma | Beam-only valid | Relay-only valid | Beam minus Relay failure | Holm p | Assessment |",
                  "| --- | ---: | ---: | ---: | ---: | --- |"])
    for key, item in contrasts.items():
        lines.append(f"| {key} | {item['beam_only_valid']} | {item['relay_only_valid']} | "
                     f"{item['beam_minus_relay_failure']:+.3f} | {item['holm_p']:.3g} | {item['assessment']} |")
    lines.extend(["", "## Full prespecified parameter grid", "",
                  "| p | gamma | profile | method | failures/shots | mean initial C2V | mean extra C2V | mean runtime ms |",
                  "| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |"])
    for rate in design["rates"]:
        for gamma in GAMMAS:
            for profile in design["profiles"]:
                for mode in MODES:
                    row = parameter_grid[rate][gamma][profile][mode]
                    lines.append(f"| {design['rates'][rate]['error_rate']:.2f} | {float(gamma[1:])/1000:.1f} | {profile} | "
                                 f"{mode} | {row['failures']}/{row['shots']} | {row['mean_initial_c2v']:.1f} | "
                                 f"{row['mean_extra_c2v']:.1f} | {row['mean_runtime_ms']:.1f} |")
    lines.extend(["", "Initial-BP baselines and every outcome count are in result.json. The per-shot "
                  "outcomes, work vectors, and observed serial runtime are in the shard ledgers.", "",
                  "## Source and budget limits", "",
                  "Relay extra units are disordered-memory legs after shared plain BP; Beam extra units are masked branches. "
                  "Their equal additional C2V cap does not make a leg and a branch compute-equivalent. "
                  "Observed runtime is serial same-process time. The source experiments used circuit-level conditions.", ""])
    markdown = "\n".join(lines)
    _write_once(output / "REPORT.md", markdown.encode())
    selected_rows = []
    grid_rows = []
    contrast_rows = []
    for rate in design["rates"]:
        for gamma in GAMMAS:
            for mode in MODES:
                row = summaries[rate][gamma][mode]
                selected_rows.append((rate, gamma, mode, row["selected_profile"],
                                      f"{row['failures']}/{row['shots']}", f"{row['mean_total_c2v']:.1f}",
                                      f"{row['mean_runtime_ms']:.1f}"))
            for profile in design["profiles"]:
                for mode in MODES:
                    row = parameter_grid[rate][gamma][profile][mode]
                    grid_rows.append((rate, gamma, profile, mode, f"{row['failures']}/{row['shots']}",
                                      f"{row['mean_initial_c2v']:.1f}", f"{row['mean_extra_c2v']:.1f}"))
    for key, row in contrasts.items():
        contrast_rows.append((key, str(row["beam_only_valid"]), str(row["relay_only_valid"]),
                              f"{row['beam_minus_relay_failure']:+.3f}", f"{row['holm_p']:.3g}",
                              row["assessment"]))
    html = ("<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><title>BB72 BeamSearch vs RelayBP</title>"
            "<style>body{font:16px system-ui;max-width:1200px;margin:3rem auto;padding:0 1rem;color:#173047}"
            "table{border-collapse:collapse;width:100%;margin:1.5rem 0}td,th{border:1px solid #bbcbd3;padding:.55rem;text-align:left}"
            "th{background:#e9f2f5}p{line-height:1.5}</style><h1>BB72 CSS BeamSearch versus RelayBP</h1>"
            "<p>Matched, independent parameter-selection and evaluation cohorts. Controlled CSS adaptation; no source-curve reproduction.</p>"
            "<h2>Selected failure and cost view</h2>"
            + _html_table(("rate", "gamma", "method", "profile", "failures/shots", "mean C2V", "runtime ms"), selected_rows)
            + "<h2>Paired contrasts</h2>"
            + _html_table(("rate/gamma", "Beam-only valid", "Relay-only valid", "failure difference", "Holm p", "assessment"), contrast_rows)
            + "<h2>Full parameter grid</h2>"
            + _html_table(("rate", "gamma", "profile", "method", "failures/shots", "initial C2V", "extra C2V"), grid_rows)
            + "<p>Full definitions, hashes, limitations, and evidence are in REPORT.md and the shard ledgers.</p></html>\n")
    _write_once(output / "study.html", html.encode())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "verify", "select", "report"))
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cohort", choices=("selection", "evaluation"))
    parser.add_argument("--rate", choices=("p050", "p080"))
    parser.add_argument("--profile", choices=("i05", "i10", "i20"))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    if args.command in ("run", "verify") and not all((args.cohort, args.rate, args.profile)):
        parser.error("run/verify require --cohort, --rate, and --profile")
    operations = {
        "prepare": lambda: prepare(args.design, args.output),
        "run": lambda: run_shard(args.design, args.output, args.cohort, args.rate, args.profile, workers=args.workers),
        "verify": lambda: run_shard(args.design, args.output, args.cohort, args.rate, args.profile,
                                    verify=True, workers=args.workers),
        "select": lambda: select(args.design, args.output, workers=args.workers),
        "report": lambda: report(args.design, args.output, workers=args.workers),
    }
    print(json.dumps(operations[args.command](), sort_keys=True))
