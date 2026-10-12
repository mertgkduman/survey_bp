#!/usr/bin/env python3
"""Measure and replay disjoint Phase 9 mechanism calibration runs."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource
import subprocess
import sys
from time import monotonic_ns


ROOT = Path(__file__).resolve().parents[1]
FAIR = ROOT / "data/studies/phase9-control-profiles-fair-v1.json"
MBBP = ROOT / "data/studies/css-literature-b1-gate-v1.json"
MASTER = ROOT / "data/studies/phase9-control-profiles-v1.json"
VERIFY_RUN_COMMAND = (
    "import json,sys; from bp_registry.cli import verify_run; "
    "print(json.dumps(verify_run(sys.argv[1]), sort_keys=True, allow_nan=False))"
)
RUN_CANONICAL_COMMAND = (
    "import json,sys; from bp_registry.cli import run_canonical; "
    "print(json.dumps(run_canonical(sys.argv[1], sys.argv[2]), sort_keys=True, allow_nan=False))"
)


def _bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def _read(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("profile input must be a JSON object")
    return value


def _digest(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError("profile artifact must be a regular non-symlink file")
    return sha256(path.read_bytes()).hexdigest()


def _publish(path: Path, payload: dict) -> None:
    value = _bytes(payload)
    if path.exists():
        if path.read_bytes() != value:
            raise ValueError("profile evidence is immutable")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _run(command: list[str]) -> tuple[dict, dict]:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = monotonic_ns()
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    wall = monotonic_ns() - start
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if process.returncode:
        raise ValueError(f"profile command failed: {process.stdout[-500:]} {process.stderr[-500:]}")
    payload = json.loads(process.stdout)
    if not isinstance(payload, dict):
        raise ValueError("public profile command did not return an object")
    cpu = round(((after.ru_utime + after.ru_stime) - (before.ru_utime + before.ru_stime)) * 1_000_000_000)
    return payload, {"wall_ns": wall, "cpu_ns": cpu, "peak_rss_bytes": after.ru_maxrss * 1024}


def _stable_verify(report: dict) -> dict:
    """Keep replay facts while excluding the verifier's invocation timestamp."""
    return {key: value for key, value in report.items() if key != "verified_at"}


def _measurement(value: int, unit: str, *, method: str, scope: str, support: str) -> dict:
    if type(value) is not int or value <= 0:
        raise ValueError("profile measurement must be a positive integer")
    return {"status": "observed", "value": value, "unit": unit,
            "method": method, "scope": scope, "support_receipt_sha256": support,
            "producer": "scripts/phase9_control_profiles.py"}


def _base_receipt(method: str, namespace: str, source: Path, replay: Path,
                  *, wall_ns: int, cpu_ns: int, replay_wall_ns: int,
                  rss_bytes: int, storage_bytes: int, evidence_bytes: int,
                  wall_method: str, cost_scope: str, work: dict) -> dict:
    source_sha = _digest(source)
    replay_sha = _digest(replay)
    measurements = {
        "execution_wall_ns": _measurement(wall_ns, "ns", method=wall_method, scope=cost_scope, support=source_sha),
        "execution_cpu_ns": _measurement(cpu_ns, "ns", method="resource.RUSAGE_CHILDREN user+system", scope=cost_scope, support=source_sha),
        "replay_wall_ns": _measurement(replay_wall_ns, "ns", method="time.monotonic_ns", scope=cost_scope, support=replay_sha),
        "peak_rss_bytes": _measurement(rss_bytes, "bytes", method="resource.RUSAGE_CHILDREN ru_maxrss", scope=cost_scope, support=source_sha),
        "storage_bytes": _measurement(storage_bytes, "bytes", method="retained regular-file sum", scope=cost_scope, support=source_sha),
        "evidence_bytes": _measurement(evidence_bytes, "bytes", method="retained canonical ledger", scope=cost_scope, support=source_sha),
    }
    return {"schema": "mechanism_profile_receipt_v1", "method": method,
            "profile_namespace": namespace, "source_receipt_path": str(source),
            "source_receipt_sha256": source_sha, "replay_receipt_path": str(replay),
            "replay_receipt_sha256": replay_sha, "verified": True,
            "publication_slurm_authorization": "deny", "assessment_status": "not_assessed",
            "mechanism_work": work, "measurements": measurements}


def _master() -> dict:
    value = _read(MASTER)
    if (value.get("schema") != "phase9_control_profiles_v1"
            or value.get("publication_slurm_authorization") != "deny"
            or value["fair_profile"]["design_sha256"] != _digest(FAIR)
            or value["mbbp_profile"]["design_sha256"] != _digest(MBBP)):
        raise ValueError("control profile design differs from prospective source bytes")
    namespaces = {value["fair_profile"]["profile_namespace"], value["mbbp_profile"]["profile_namespace"],
                  value["schedule_profile"]["profile_namespace"]}
    if len(namespaces) != 3 or namespaces & set(value["evaluation_namespaces"]):
        raise ValueError("profile and evaluation namespaces must be disjoint")
    return value


def run_fair(output: Path) -> dict:
    design = _master()
    fair_root = output / "fair-v2"
    public_run, run_cost = _run([sys.executable, str(ROOT / "scripts/run_fair_beam_relay_css.py"),
                                 "run", "--design", str(FAIR), "--output", str(fair_root)])
    _publish(fair_root / "public-run.json", public_run)
    public_verify, replay_cost = _run([sys.executable, str(ROOT / "scripts/run_fair_beam_relay_css.py"),
                                       "verify", "--design", str(FAIR), "--output", str(fair_root)])
    _publish(fair_root / "public-verify.json", public_verify)
    if public_run != public_verify or public_verify.get("shots") != 1:
        raise ValueError("fair mechanism replay differs from one frozen calibration shot")
    ledger = fair_root / "events.jsonl"
    rows = ledger.read_text().splitlines()
    if len(rows) != 1:
        raise ValueError("fair profile requires one complete ledger row")
    row = json.loads(rows[0])
    arm = row["arms"][design["fair_profile"]["damping_arm"]]
    files = tuple(path for path in fair_root.rglob("*") if path.is_file() and not path.is_symlink())
    for method in ("beam", "relay"):
        runtime = arm["runtime_ns"]
        wall = runtime["initial"] + runtime[f"{method}_extra"]
        work = arm[method]["total_work"]
        receipt = _base_receipt(
            method, design["fair_profile"]["profile_namespace"], ledger, fair_root / "public-verify.json",
            wall_ns=run_cost["wall_ns"], cpu_ns=run_cost["cpu_ns"], replay_wall_ns=replay_cost["wall_ns"],
            rss_bytes=run_cost["peak_rss_bytes"], storage_bytes=sum(path.stat().st_size for path in files),
            evidence_bytes=ledger.stat().st_size,
            wall_method="time.monotonic_ns:full_public_paired_process_upper_bound",
            cost_scope="one BB72 matched shot; method inner wall/work, full paired-process wall/CPU/RSS/storage upper bound",
            work=work,
        )
        receipt["measurements"]["mechanism_inner_wall_ns"] = _measurement(
            wall, "ns", method="time.perf_counter_ns:serial_same_process_v1",
            scope="shared initial BP plus declared mechanism continuation",
            support=_digest(ledger),
        )
        _publish(output / f"{method}-profile-v2.json", receipt)
    return {"status": "ok", "methods": ["beam", "relay"], "ledger_sha256": _digest(ledger)}


def run_mbbp(output: Path) -> dict:
    design = _master()
    mbbp_root = output / "mbbp"
    public_run, run_cost = _run([sys.executable, str(ROOT / "scripts/run_css_literature_gate.py"),
                                 "vote", "--study", str(MBBP), "--output", str(mbbp_root)])
    _publish(mbbp_root / "public-run.json", public_run)
    run_root = Path(public_run["output"])
    if not run_root.is_relative_to(mbbp_root.resolve()) or public_run.get("final_row_count") != 2:
        raise ValueError("MBBP profile lacks its bounded two-shot public run")
    public_verify, replay_cost = _run([sys.executable, "-c", VERIFY_RUN_COMMAND, str(run_root)])
    public_verify = _stable_verify(public_verify)
    _publish(mbbp_root / "public-verify.json", public_verify)
    if public_verify.get("final_row_count") != 2:
        raise ValueError("MBBP profile replay changed the frozen denominator")
    ledger = run_root / "events.jsonl"
    files = tuple(path for path in run_root.rglob("*") if path.is_file() and not path.is_symlink())
    receipt = _base_receipt(
        "mbbp", design["mbbp_profile"]["profile_namespace"], ledger, mbbp_root / "public-verify.json",
        wall_ns=run_cost["wall_ns"], cpu_ns=run_cost["cpu_ns"], replay_wall_ns=replay_cost["wall_ns"],
        rss_bytes=run_cost["peak_rss_bytes"], storage_bytes=sum(path.stat().st_size for path in files),
        evidence_bytes=ledger.stat().st_size, wall_method="time.monotonic_ns",
        cost_scope="two-shot public B1 vote adaptation run, including both BP members",
        work={"status": "recorded_in_verified_public_ledger"},
    )
    _publish(output / "mbbp-profile.json", receipt)
    return {"status": "ok", "method": "mbbp", "ledger_sha256": _digest(ledger)}


def derive_mbbp_work(output: Path) -> dict:
    """Bind per-shot member work to the already retained MBBP profile."""
    source = _read(output / "mbbp-profile.json")
    ledger = Path(source["source_receipt_path"])
    if source["source_receipt_sha256"] != _digest(ledger):
        raise ValueError("MBBP profile ledger changed before work derivation")
    by_shot: dict[int, int] = {}
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row["kind"] != "work_leaf":
            continue
        vector = row["data"]["payload"]["work_vector"]
        amount = sum(value for value in vector.values() if type(value) is int)
        if amount < 0:
            raise ValueError("MBBP work leaf is negative")
        shot = row["shot_id"]
        by_shot[shot] = by_shot.get(shot, 0) + amount
    if set(by_shot) != {0, 1} or min(by_shot.values()) <= 0:
        raise ValueError("MBBP profile lacks both per-shot member work totals")
    derived = {**source, "mechanism_work": {
        "status": "observed", "unit": "summed_work_vector_units",
        "scope": "one shared member ensemble before list or vote decision",
        "by_shot": {str(shot): amount for shot, amount in sorted(by_shot.items())},
        "per_pair_projection_upper_bound": max(by_shot.values()),
        "support_receipt_sha256": _digest(ledger),
    }}
    _publish(output / "mbbp-profile-v2.json", derived)
    return {"status": "ok", "method": "mbbp", "per_pair_work_upper_bound": max(by_shot.values())}


def run_schedule(output: Path) -> dict:
    design = _master()
    manifests = design["schedule_profile"]["source_manifest_paths"]
    for method in ("spa_flooding", "spa_check_node_serial"):
        manifest = (ROOT / manifests[method]).resolve(strict=True)
        if not manifest.is_relative_to((ROOT / "data/results/phase3-pilots/manifests").resolve()):
            raise ValueError("schedule profile manifest escaped the tracked Phase 3 inputs")
        source = output / "schedule" / method
        public_run, run_cost = _run([sys.executable, "-c", RUN_CANONICAL_COMMAND,
                                     str(manifest), str(source)])
        if public_run.get("final_row_count") != 1:
            raise ValueError("schedule calibration did not complete one prospective shot")
        _publish(source / "public-run.json", public_run)
        public_verify, replay_cost = _run([sys.executable, "-c", VERIFY_RUN_COMMAND, str(source)])
        public_verify = _stable_verify(public_verify)
        if public_verify.get("final_row_count") != 1:
            raise ValueError("schedule calibration does not have one verified terminal")
        replay = output / f"{method}-public-verify.json"
        _publish(replay, public_verify)
        ledger = source / "events.jsonl"
        events = [json.loads(row) for row in ledger.read_text().splitlines()]
        runtime = [row["data"]["profile"]["runtime"] for row in events if row["kind"] == "runtime"]
        works = [row["data"]["work_vector"] for row in events if row["kind"] == "work"]
        if len(runtime) != 1 or len(works) != 1:
            raise ValueError("schedule calibration has missing runtime or work")
        observed = runtime[0]
        files = tuple(path for path in source.rglob("*") if path.is_file() and not path.is_symlink())
        receipt = _base_receipt(
            method, design["schedule_profile"]["profile_namespace"], ledger, replay,
            wall_ns=run_cost["wall_ns"], cpu_ns=run_cost["cpu_ns"],
            replay_wall_ns=replay_cost["wall_ns"],
            rss_bytes=run_cost["peak_rss_bytes"],
            storage_bytes=sum(path.stat().st_size for path in files), evidence_bytes=ledger.stat().st_size,
            wall_method="time.monotonic_ns:full_public_process_upper_bound",
            cost_scope="one newly verified shot from tracked Phase 3 B1 p=0.03 manifest; evaluation p=0.10 projection only",
            work=works[0],
        )
        receipt["measurements"]["mechanism_inner_wall_ns"] = _measurement(
            observed["wall_time"]["value"], "ns", method=observed["wall_time"]["method"],
            scope="canonical decoder inner wall", support=_digest(ledger))
        _publish(output / f"{method}-profile.json", receipt)
    return {"status": "ok", "methods": ["spa_flooding", "spa_check_node_serial"]}


def verify(output: Path) -> dict:
    design = _master()
    fair_replay, _ = _run([sys.executable, str(ROOT / "scripts/run_fair_beam_relay_css.py"),
                           "verify", "--design", str(FAIR), "--output", str(output / "fair-v2")])
    if fair_replay != _read(output / "fair-v2/public-verify.json"):
        raise ValueError("fair public replay changed after profile publication")
    mbbp_source = _read(output / "mbbp-profile.json")["source_receipt_path"]
    mbbp_replay, _ = _run([sys.executable, "-c", VERIFY_RUN_COMMAND,
                           str(Path(mbbp_source).parent)])
    if _stable_verify(mbbp_replay) != _read(output / "mbbp/public-verify.json"):
        raise ValueError("MBBP public replay changed after profile publication")
    for method in design["schedule_profile"]["source_manifest_paths"]:
        schedule_replay, _ = _run([sys.executable, "-c", VERIFY_RUN_COMMAND,
                                   str(output / "schedule" / method)])
        if _stable_verify(schedule_replay) != _read(output / f"{method}-public-verify.json"):
            raise ValueError("schedule public replay changed after profile publication")
    for method in ("beam", "relay", "mbbp", "spa_flooding", "spa_check_node_serial"):
        receipt_name = (f"{method}-profile-v2.json" if method in {"beam", "relay", "mbbp"}
                        else f"{method}-profile.json")
        receipt = _read(output / receipt_name)
        profile_kind = ("mbbp_profile" if method == "mbbp" else
                        "schedule_profile" if method.startswith("spa_") else "fair_profile")
        expected_namespace = design[profile_kind]["profile_namespace"]
        if (receipt.get("schema") != "mechanism_profile_receipt_v1" or receipt.get("method") != method
                or receipt.get("profile_namespace") != expected_namespace
                or receipt.get("verified") is not True
                or receipt.get("publication_slurm_authorization") != "deny"
                or receipt.get("assessment_status") != "not_assessed"
                or receipt.get("source_receipt_sha256") != _digest(Path(receipt["source_receipt_path"]))
                or receipt.get("replay_receipt_sha256") != _digest(Path(receipt["replay_receipt_path"]))):
            raise ValueError("profile receipt differs from retained source or replay evidence")
        for name, item in receipt["measurements"].items():
            if item.get("status") != "observed" or type(item.get("value")) is not int or item["value"] <= 0:
                raise ValueError("profile has an unavailable or invalid measurement")
        if method in {"beam", "relay"}:
            rows = (output / "fair-v2/events.jsonl").read_text().splitlines()
            arm = json.loads(rows[0])["arms"][design["fair_profile"]["damping_arm"]]
            if receipt["measurements"]["mechanism_inner_wall_ns"]["value"] != arm["runtime_ns"]["initial"] + arm["runtime_ns"][f"{method}_extra"]:
                raise ValueError("fair method inner wall differs from retained event")
            if receipt["measurements"]["execution_wall_ns"]["value"] < receipt["measurements"]["mechanism_inner_wall_ns"]["value"]:
                raise ValueError("fair full-process wall cannot be smaller than method inner wall")
        if method == "mbbp":
            expected_work = derive_mbbp_work(output)
            if receipt["mechanism_work"]["per_pair_projection_upper_bound"] != expected_work["per_pair_work_upper_bound"]:
                raise ValueError("MBBP member work differs from verified ledger")
    return {"status": "verified", "methods": ["beam", "relay", "mbbp", "spa_flooding", "spa_check_node_serial"],
            "publication_slurm_authorization": "deny"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run-fair", "run-mbbp", "derive-mbbp-work", "run-schedule", "verify"))
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    result = {"run-fair": run_fair, "run-mbbp": run_mbbp, "derive-mbbp-work": derive_mbbp_work,
              "run-schedule": run_schedule, "verify": verify}[args.command](root)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
