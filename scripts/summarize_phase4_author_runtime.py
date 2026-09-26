#!/usr/bin/env python3
"""Summarize retained matched Relay v0.2.2 pipeline timings.

This is a derived diagnostic over the immutable author-agreement shots.  It
does not time either decoder anew or equate their different timing boundaries.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping


AUTHOR_PIN = "relay-v0.2.2@14cb31a18f9b9d7d099791b793e35b8a2951f8f3"


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _timing(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("timing comparison requires complete positive finite observations")
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p95_linear": _quantile(values, .95),
        "max": max(values),
        "total": sum(values),
    }


def summarize_author_runtime(agreement_root: Path) -> dict[str, Any]:
    """Require every prespecified pair and retain the distinct timing scopes."""
    agreement_root = agreement_root.resolve()
    report_path = agreement_root / "result.json"
    report_bytes = report_path.read_bytes()
    report = _read_object(report_path)
    if report.get("status") != "completed" or report.get("author_source_pin") != AUTHOR_PIN:
        raise ValueError("author agreement must be completed at the approved source pin")
    report_digest = report.get("result_digest")
    if report_digest != _digest({key: value for key, value in report.items() if key != "result_digest"}):
        raise ValueError("author agreement report digest does not verify")
    look_shots = report.get("look_shots")
    codes = report.get("codes")
    if not isinstance(look_shots, int) or look_shots < 1 or not isinstance(codes, Mapping) or not codes:
        raise ValueError("author agreement omits its finite code and shot plan")
    native_origin = report.get("native_module_origin")
    native_environment = report.get("native_environment_path")
    if (not isinstance(native_origin, str) or not isinstance(native_environment, str)
            or not Path(native_origin).resolve().is_relative_to(Path(native_environment).resolve())):
        raise ValueError("author module origin is outside the isolated native environment")

    summaries: dict[str, Any] = {}
    for code_id in sorted(codes):
        expected = codes[code_id]
        if not isinstance(expected, Mapping) or expected.get("complete_pairs") != look_shots or expected.get("incomplete_pair_shot_ids"):
            raise ValueError(f"{code_id} author agreement has an incomplete paired denominator")
        canonical_seconds: list[float] = []
        native_seconds: list[float] = []
        ratios: list[float] = []
        success_pairs = {f"canonical_{c}_native_{n}": 0 for c in (0, 1) for n in (0, 1)}
        exact_candidate_disagreements = 0
        gamma_checks = 0
        for shot_id in range(look_shots):
            shot = _read_object(agreement_root / code_id / f"shot-{shot_id:04d}" / "result.json")
            if shot.get("code_id") != code_id or shot.get("shot_id") != shot_id:
                raise ValueError(f"{code_id} shot {shot_id} identity mismatch")
            canonical, native = shot.get("canonical"), shot.get("native")
            if not isinstance(canonical, Mapping) or not isinstance(native, Mapping) or canonical.get("status") != "completed" or native.get("status") != "completed":
                raise ValueError(f"{code_id} shot {shot_id} is not a complete paired observation")
            if canonical.get("sample_identity") != native.get("sample_identity") or not canonical.get("sample_identity"):
                raise ValueError(f"{code_id} shot {shot_id} does not match physical sample identity")
            if native.get("native_module_origin") != native_origin:
                raise ValueError(f"{code_id} shot {shot_id} uses a different native module")
            canonical_elapsed = canonical.get("public_boundary", {}).get("elapsed_seconds")
            native_elapsed = native.get("runtime_seconds")
            if (not isinstance(canonical_elapsed, (int, float)) or not isinstance(native_elapsed, (int, float))
                    or not math.isfinite(canonical_elapsed) or not math.isfinite(native_elapsed)
                    or canonical_elapsed <= 0 or native_elapsed <= 0):
                raise ValueError(f"{code_id} shot {shot_id} lacks finite positive timing")
            canonical_seconds.append(float(canonical_elapsed))
            native_seconds.append(float(native_elapsed))
            ratios.append(float(canonical_elapsed) / float(native_elapsed))
            canonical_success = int(canonical.get("diagnostic_cell") == "valid_correct")
            native_success = int(native.get("diagnostic_cell") == "valid_correct")
            success_pairs[f"canonical_{canonical_success}_native_{native_success}"] += 1
            exact_candidate_disagreements += canonical.get("diagnostic_candidate_sha256") != native.get("diagnostic_candidate_sha256")
            checks = shot.get("executed_gamma_digests_checked")
            if not isinstance(checks, int) or checks < 0:
                raise ValueError(f"{code_id} shot {shot_id} omits gamma verification count")
            gamma_checks += checks
        if (success_pairs != expected.get("paired_success_table")
                or exact_candidate_disagreements != expected.get("disagreement", {}).get("exact_candidate", {}).get("count")
                or gamma_checks != expected.get("executed_gamma_digests_checked")):
            raise ValueError(f"{code_id} retained pairs do not reconstruct the agreement report")
        summaries[code_id] = {
            "paired_shots": look_shots,
            "canonical_public_seconds": _timing(canonical_seconds),
            "native_pipeline_seconds": _timing(native_seconds),
            "paired_canonical_over_native_ratio": _timing(ratios),
            "canonical_slower_pairs": sum(canonical > native for canonical, native in zip(canonical_seconds, native_seconds, strict=True)),
            "paired_success_table": success_pairs,
            "exact_candidate_disagreements": exact_candidate_disagreements,
            "executed_gamma_digests_checked": gamma_checks,
        }

    summary: dict[str, Any] = {
        "schema_version": 1,
        "status": "completed_derived_diagnostic",
        "author_source_pin": AUTHOR_PIN,
        "agreement_report_byte_sha256": sha256(report_bytes).hexdigest(),
        "agreement_result_digest": report_digest,
        "timing_scopes": {
            "canonical_public_seconds": "public canonical CLI run plus mandatory verify-canonical-shot; excludes later diagnostic classification",
            "native_pipeline_seconds": "canonical-observation, gamma reconstruction, isolated author process and decode, plus diagnostic classification",
            "paired_canonical_over_native_ratio": "ratio of the two recorded unequal pipeline boundaries for each matched shot",
        },
        "claim_limit": "Recorded paired pipeline timing only; unequal boundaries and fixed canonical-first order do not isolate decoder-kernel or programming-language speed.",
        "codes": summaries,
    }
    summary["summary_digest"] = _digest(summary)
    return summary


def write_summary(agreement_root: Path) -> Path:
    """Write an idempotent derivative without modifying the source report."""
    summary = summarize_author_runtime(agreement_root)
    destination = agreement_root / "runtime-comparison.json"
    payload = (json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if destination.exists():
        if destination.read_bytes() != payload:
            raise FileExistsError("refusing to overwrite a different runtime comparison")
        return destination
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agreement-root", type=Path, default=Path("data/results/phase4-memory-relay/author-v022-agreement-v1"))
    args = parser.parse_args()
    output = write_summary(args.agreement_root)
    print(output)


if __name__ == "__main__":
    main()
