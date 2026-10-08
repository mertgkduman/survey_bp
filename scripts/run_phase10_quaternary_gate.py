#!/usr/bin/env python3
"""Freeze, run, and independently verify Phase 10's bounded D-13 evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import numpy as np

from bp_registry.css import CssCode
from bp_registry.quaternary.algebra import syndrome as pauli_syndrome
from bp_registry.quaternary.asced import AscedController, AscedSpec, construct_splitter_batch, materialize_asced_batches
from bp_registry.quaternary.asced_overcomplete import construct_overcomplete_map
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.native_asced import admit_phase10_native_asced_evidence
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


ROOT = Path(__file__).resolve().parents[1]
_SPLITTER_RECEIPT = "d28362b1d8b97eb01768d8fd33c7f6d04c1050ad828b767c5ebb089da59c8fc9"
_MAP_RECEIPT = "9f40262f7afe0f109759871179b86b369f42711bd607248f87461db7dc2a4177"
_H_EXT = "2a50c370f69f9f751e711fd97dd48178844c14bc2117d85e31f12af0f70c6355"
_MAPPING = "4c1c8b14e7a64e1841b2710c93f774638334a776ab33e86e5cb6d6fcfa9b0453"
_H_OC = "105463db1e405e01cfea9064c3247cbb6902c48d34fcd5b86b162cdc60c8d768"
_COMMIT = "816772071486615dfc7d71d1e15df597edc58a26"


def _fail(message: str) -> None:
    raise ValueError(message)


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        _fail(f"required JSON file is absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _record(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    raw = {"kind": kind, "data": data}
    return {**raw, "event_id": f"phase10-{_digest(raw)[:20]}"}


def _fixture_batch(study: dict[str, Any], asced: dict[str, Any]):
    """Rebuild and compare the complete constructed splitter/map pair before any shot."""
    pair = asced.get("constructed_receipt_pair")
    if not isinstance(pair, dict):
        _fail("aSCED manifest lacks the constructed receipt pair")
    fixture = _load(ROOT / str(pair.get("splitter_fixture", "")))
    map_fixture = _load(ROOT / str(pair.get("overcomplete_map_fixture", "")))
    if fixture.get("run_fidelity") != "canonical_adaptation" or map_fixture.get("run_fidelity") != "canonical_adaptation":
        _fail("canonical aSCED fixture and map must remain canonical_adaptation")
    receipt = fixture.get("receipt")
    map_receipt = map_fixture.get("receipt")
    if not isinstance(receipt, dict) or not isinstance(map_receipt, dict):
        _fail("constructed aSCED receipts are incomplete")
    expected = {
        "constructed_splitter_receipt_sha256": _SPLITTER_RECEIPT,
        "constructed_map_receipt_sha256": _MAP_RECEIPT,
        "h_ext_sha256": _H_EXT,
        "mapping_sha256": _MAPPING,
        "h_oc_sha256": _H_OC,
    }
    observed = {
        "constructed_splitter_receipt_sha256": receipt.get("constructed_receipt_sha256"),
        "constructed_map_receipt_sha256": map_receipt.get("receipt_sha256"),
        "h_ext_sha256": receipt.get("h_ext_sha256"),
        "mapping_sha256": map_receipt.get("mapping_sha256"),
        "h_oc_sha256": map_receipt.get("h_oc_sha256"),
    }
    if observed != expected or {key: pair.get(key) for key in expected} != expected:
        _fail("constructed splitter/map receipt digest pair differs from the admitted canonical pair")
    typed_h_ext = np.asarray(fixture.get("h_ext"), dtype=np.uint8)
    if fixture.get("h_ext") != map_fixture.get("h_ext") or fixture.get("h_ext_row_map") != map_fixture.get("h_ext_row_map"):
        _fail("constructed splitter and map do not retain byte-identical typed H_ext and row origins")
    if pair.get("row_order") != ["H_X", "T_X", "H_Z", "T_Z"] or map_fixture.get("row_order") != ["H_X", "T_X", "H_Z", "T_Z"]:
        _fail("aSCED row order must be [H_X,T_X,H_Z,T_Z]")
    rows = typed_h_ext
    origins = fixture["h_ext_row_map"]
    hx = np.vstack([(rows[index] == 1).astype(np.uint8) for index, row in enumerate(origins) if row[:2] == ["x", "original"]])
    hz = np.vstack([(rows[index] == 3).astype(np.uint8) for index, row in enumerate(origins) if row[:2] == ["z", "original"]])
    batch = construct_splitter_batch(CssCode(hx, hz).validate(), delta=2, row_weight=4, attempt_cap=10_000)
    if not hasattr(batch, "receipt"):
        _fail("canonical splitter reconstruction exhausted")
    if batch.h_ext.tolist() != fixture["h_ext"] or [list(row) for row in batch.h_ext_row_map] != origins:
        _fail("reconstructed canonical H_ext or typed row origins differ from the frozen fixture")
    if batch.receipt.receipt_sha256 != _SPLITTER_RECEIPT:
        _fail("reconstructed constructed splitter receipt differs")
    made = construct_overcomplete_map(batch, pair_cap=1000)
    if not isinstance(made, tuple):
        _fail("canonical overcomplete construction exhausted")
    overcomplete, map_receipt_obj, _searches = made
    if (overcomplete.h_ext.tolist() != (np.asarray(map_fixture["h_ext"], dtype=np.uint8) != 0).astype(np.uint8).tolist()
            or overcomplete.mapping.tolist() != map_fixture["mapping"]
            or overcomplete.h_oc.tolist() != map_fixture["h_oc"] or map_receipt_obj.receipt_sha256 != _MAP_RECEIPT):
        _fail("reconstructed canonical overcomplete map differs from the frozen fixture")
    return batch, overcomplete, map_receipt_obj, _searches


def _validate(study_path: Path, native_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], Any, Any, Any, Any]:
    study = _load(study_path)
    if study.get("schema") != "phase10-quaternary-mechanism-study-v1":
        _fail("Phase 10 study schema is not admitted")
    if study.get("profile") != {"code": "GB46", "physical_error_rate": 0.05, "canonical_seed": 10}:
        _fail("Phase 10 study must freeze GB46, p=0.05, and canonical seed 10")
    if study.get("admitted_shot_ids") != list(range(256)):
        _fail("Phase 10 study must admit exactly shot IDs 0..255")
    if study.get("arms") != ["bp4", "asced_ordinary", "asced_overcomplete"]:
        _fail("Phase 10 study must use exactly the three canonical arms")
    if study.get("assessment") != "not_assessed" or study.get("phase11_boundary") != "no_curve_reproduction_or_performance_ranking":
        _fail("Phase 10 evidence must remain not_assessed and outside Phase 11 ranking")
    if study.get("channel", {}).get("probabilities") != [0.95, 0.05 / 3, 0.05 / 3, 0.05 / 3]:
        _fail("Phase 10 study must retain equal-proportion p=0.05 channel probabilities")
    bp4 = _load(ROOT / str(study.get("bp4_manifest", "")))
    asced = _load(ROOT / str(study.get("asced_manifest", "")))
    if bp4.get("run_fidelity") != "canonical_adaptation" or asced.get("run_fidelity") != "canonical_adaptation":
        _fail("canonical arms must be labelled canonical_adaptation")
    if bp4.get("iteration_cap") != 25 or asced.get("ordinary", {}).get("iteration_cap") != 25 or asced.get("overcomplete", {}).get("iteration_cap") != 12:
        _fail("canonical BP4 caps must remain 25/25/12")
    if asced.get("ordinary", {}).get("L") != 1 or asced.get("ordinary", {}).get("Delta") != 2 or asced.get("overcomplete", {}).get("L") != 1 or asced.get("overcomplete", {}).get("Delta") != 2:
        _fail("aSCED must retain L=1 and Delta=2")
    if asced.get("ordinary", {}).get("paths_per_shot") != 4 or asced.get("overcomplete", {}).get("paths_per_shot") != 4:
        _fail("each aSCED arm must retain all four virtual paths")
    native_requirement = study.get("native_requirement")
    if not isinstance(native_requirement, dict) or native_requirement.get("required_terminal") != "native_success":
        _fail("study must require the successful native aSCED terminal")
    native = admit_phase10_native_asced_evidence(native_path, spec_path=ROOT / str(native_requirement.get("source_spec", "")))
    aggregate = native.get("aggregate")
    if (native.get("native_identity", {}).get("commit") != _COMMIT or native.get("workers") != 1
            or native.get("max_trials") != 10000 or native.get("target_errors") != 10
            or not isinstance(aggregate, dict) or not isinstance(aggregate.get("trials"), int)
            or not isinstance(aggregate.get("logical_errors"), int)):
        _fail("native aSCED terminal does not retain the required exact aggregate facts")
    batch, overcomplete, map_receipt, searches = _fixture_batch(study, asced)
    return study, bp4, asced, native, batch, overcomplete, map_receipt, searches


def _sample(seed: int, shot_id: int, probabilities: list[float], n: int) -> np.ndarray:
    identity = f"phase10-quaternary-b1-gate:seed:{seed}:shot:{shot_id}"
    rng = np.random.Generator(np.random.PCG64(int.from_bytes(sha256(identity.encode()).digest()[:16], "big")))
    return np.asarray(rng.choice(4, size=n, p=np.asarray(probabilities, dtype=np.float64)), dtype=np.uint8)


def _outcome(original: QuaternaryOriginalProblem, hidden: np.ndarray, candidate: np.ndarray | None) -> str:
    if candidate is None or not np.array_equal(original.code.syndrome(candidate), original.syndrome):
        return "invalid_syndrome"
    return "exact" if np.array_equal(hidden, candidate) else "logical_failure"


def _path_payload(path: Any, original: QuaternaryOriginalProblem, sample_digest: str, arm: str) -> dict[str, Any]:
    return {
        "arm": arm, "shot_id": None, "sample_digest": sample_digest, "batch_index": path.batch_index,
        "path_index": path.path_index, "virtual_bits_lsb_first": list(path.virtual_bits),
        "z_ext_order": "[s_X,g_X,s_Z,g_Z]", "extended_syndrome": list(path.extended_syndrome),
        "original_syndrome": original.syndrome.tolist(), "candidate": list(path.candidate),
        "extended_valid": path.extended_valid, "original_valid": path.original_valid,
        "terminal": path.terminal, "work": path.work.as_evidence(structural_event_version=4),
        "overcomplete_map_receipt": path.overcomplete_map_receipt, "assessment": "not_assessed",
    }


def run(study_path: Path, native_path: Path, output: Path) -> None:
    study, bp4, asced, native, batch, overcomplete, map_receipt, searches = _validate(study_path, native_path)
    if output.exists() and any(output.iterdir()):
        _fail(f"run-once output already exists and is nonempty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    channel = study["channel"]["probabilities"]
    events: list[dict[str, Any]] = []
    kernel = ScalarLlrBp4Kernel()
    for shot_id in study["admitted_shot_ids"]:
        hidden = _sample(10, shot_id, channel, batch.code.n)
        sample_digest = sha256(hidden.tobytes()).hexdigest()
        code = compile_css_artifact(batch.code, source_artifact_identity="pinned-gb46-h44")
        syndrome = code.syndrome(hidden)
        original = QuaternaryOriginalProblem(
            f"original-phase10-gb46-{shot_id}", code, syndrome,
        )
        priors = np.tile(np.asarray(channel, dtype=np.float64), (batch.code.n, 1))
        priors = np.maximum(priors, float(bp4["decoder_smoothing"])); priors /= priors.sum(axis=1, keepdims=True)
        baseline = kernel.new_session(original, priors).run(max_iterations=25)
        events.append(_record("canonical_terminal", {
            "arm": "bp4", "shot_id": shot_id, "sample_digest": sample_digest, "candidate": baseline.candidate.tolist(),
            "original_syndrome": syndrome.tolist(), "terminal": baseline.terminal,
            "outcome": _outcome(original, hidden, baseline.candidate), "work": baseline.work.as_evidence(structural_event_version=4),
            "iteration_cap": 25, "run_fidelity": "canonical_adaptation", "assessment": "not_assessed",
        }))
        batches = materialize_asced_batches(original, (batch,), path_cap=4)
        for arm, cap, maps in (("asced_ordinary", 25, None), ("asced_overcomplete", 12, {batches[0].batch_id: (overcomplete, map_receipt, searches)})):
            result = AscedController(AscedSpec(max_iterations=cap, path_cap=4, max_total_bp_calls=int(asced["ordinary"]["max_work"]))).run(
                original, batches, priors, kernel=kernel, overcomplete=maps,
            )
            if len(result.paths) != 4:
                _fail("aSCED execution did not retain exactly four virtual paths")
            events.append(_record("canonical_terminal", {
                "arm": arm, "shot_id": shot_id, "sample_digest": sample_digest,
                "candidate": None if result.selected_candidate is None else list(result.selected_candidate),
                "original_syndrome": syndrome.tolist(), "terminal": result.termination,
                "outcome": _outcome(original, hidden, None if result.selected_candidate is None else np.asarray(result.selected_candidate, dtype=np.uint8)),
                "work": result.work.as_evidence(structural_event_version=4), "iteration_cap": cap,
                "run_fidelity": result.run_fidelity, "assessment": "not_assessed",
                "constructed_splitter_receipt_sha256": batch.receipt.receipt_sha256,
                "constructed_map_receipt_sha256": None if maps is None else map_receipt.receipt_sha256,
            }))
            for path in result.paths:
                payload = _path_payload(path, original, sample_digest, arm)
                payload["shot_id"] = shot_id
                events.append(_record("asced_path", payload))
    ledger = output / "canonical-ledger.jsonl"
    ledger.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")
    receipt = {
        "schema": "phase10-quaternary-mechanism-run-v1", "study_sha256": _digest(study),
        "canonical_ledger_sha256": sha256(ledger.read_bytes()).hexdigest(), "canonical_terminal_count": 768,
        "asced_path_terminal_count": 2048, "assessment": "not_assessed",
        "native_aggregate": {"trials": native["aggregate"]["trials"], "logical_errors": native["aggregate"]["logical_errors"], "sample_matching": "unavailable_aggregate_only"},
        "constructed_receipt_pair": {"splitter": _SPLITTER_RECEIPT, "map": _MAP_RECEIPT, "h_ext": _H_EXT, "mapping": _MAPPING, "h_oc": _H_OC},
    }
    (output / "study-receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def verify(study_path: Path, native_path: Path, output: Path, *, replay: bool = False) -> None:
    """Verify retained structure and, explicitly, regenerate decoder output.

    Event hashes bind submitted payloads only.  Decoder-result verification is
    therefore unavailable until the full frozen batch is replayed.
    """
    study, _bp4, _asced, native, batch, overcomplete, _map_receipt, searches = _validate(study_path, native_path)
    ledger = output / "canonical-ledger.jsonl"; receipt_path = output / "study-receipt.json"
    if not ledger.is_file() or not receipt_path.is_file():
        _fail("persisted run output is incomplete")
    receipt = _load(receipt_path)
    lines = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    if (receipt.get("schema") != "phase10-quaternary-mechanism-run-v1"
            or receipt.get("study_sha256") != _digest(study)
            or receipt.get("canonical_ledger_sha256") != sha256(ledger.read_bytes()).hexdigest()
            or receipt.get("canonical_terminal_count") != 768
            or receipt.get("asced_path_terminal_count") != 2048
            or receipt.get("assessment") != "not_assessed"
            or receipt.get("constructed_receipt_pair") != {
                "splitter": _SPLITTER_RECEIPT, "map": _MAP_RECEIPT, "h_ext": _H_EXT,
                "mapping": _MAPPING, "h_oc": _H_OC,
            }):
        _fail("persisted study receipt digest differs from the frozen design or ledger")
    event_ids: set[str] = set()
    for event in lines:
        event_id = event.get("event_id")
        raw = {"kind": event.get("kind"), "data": event.get("data")}
        if not isinstance(event_id, str) or event_id != f"phase10-{_digest(raw)[:20]}" or event_id in event_ids:
            _fail("ledger event identity is missing, duplicated, or does not bind its payload")
        event_ids.add(event_id)
    if not replay:
        _fail("canonical decoder output requires explicit --replay verification")
    terminals = [event["data"] for event in lines if event.get("kind") == "canonical_terminal"]
    paths = [event["data"] for event in lines if event.get("kind") == "asced_path"]
    if len(terminals) != 768 or len(paths) != 2048:
        _fail("persisted evidence does not contain exactly 768 canonical terminals and 2048 aSCED paths")
    original_code = compile_css_artifact(batch.code, source_artifact_identity="pinned-gb46-h44")
    overcomplete_checks = np.array(batch.h_ext, dtype=np.uint8, copy=True)
    for index, search in enumerate(searches):
        pauli = 1 if search.role == "x" else 3
        overcomplete_checks = np.vstack((overcomplete_checks, np.where(overcomplete.h_oc[len(batch.h_ext) + index], pauli, 0).astype(np.uint8)))
    by_shot: dict[int, dict[str, str]] = {}
    expected_syndromes: dict[int, np.ndarray] = {}
    for terminal in terminals:
        if terminal.get("assessment") != "not_assessed" or terminal.get("run_fidelity") != "canonical_adaptation":
            _fail("canonical terminal assessment or fidelity drifted")
        shot = terminal.get("shot_id"); arm = terminal.get("arm"); digest = terminal.get("sample_digest")
        if not isinstance(shot, int) or arm not in study["arms"] or not isinstance(digest, str):
            _fail("canonical terminal identity is incomplete")
        expected_hidden = _sample(10, shot, study["channel"]["probabilities"], 46)
        expected_syndrome = original_code.syndrome(expected_hidden)
        candidate = terminal.get("candidate")
        if candidate is None:
            if arm == "bp4":
                _fail("standalone BP4 terminal must retain a 46-qubit Pauli candidate")
            candidate_array = None
        else:
            if (not isinstance(candidate, list) or len(candidate) != 46
                    or any(type(value) is not int or not 0 <= value <= 3 for value in candidate)):
                _fail("canonical terminal candidate is not a 46-qubit Pauli vector")
            candidate_array = np.asarray(candidate, dtype=np.uint8)
        original = QuaternaryOriginalProblem(f"original-phase10-verify-{shot}", original_code, expected_syndrome)
        if (digest != sha256(expected_hidden.tobytes()).hexdigest()
                or terminal.get("original_syndrome") != expected_syndrome.tolist()
                or terminal.get("outcome") != _outcome(original, expected_hidden, candidate_array)
                or not terminal.get("work")):
            _fail("canonical terminal sample reconstruction or retained work check failed")
        expected_syndromes[shot] = expected_syndrome
        by_shot.setdefault(shot, {})[arm] = digest
    if set(by_shot) != set(range(256)) or any(set(arms) != set(study["arms"]) or len(set(arms.values())) != 1 for arms in by_shot.values()):
        _fail("canonical arms do not share exactly one physical sample for every admitted shot")
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for path in paths:
        if path.get("assessment") != "not_assessed" or path.get("z_ext_order") != "[s_X,g_X,s_Z,g_Z]":
            _fail("aSCED path assessment or typed virtual-syndrome order drifted")
        key = (path.get("shot_id"), path.get("arm")); grouped.setdefault(key, []).append(path)
    for shot in range(256):
        for arm in ("asced_ordinary", "asced_overcomplete"):
            group = grouped.get((shot, arm), [])
            if len(group) != 4 or {item.get("path_index") for item in group} != {0, 1, 2, 3}:
                _fail("each aSCED arm must retain paths 0..3 for every admitted shot")
            if any(item.get("sample_digest") != by_shot[shot][arm] for item in group):
                _fail("aSCED path sample identity differs from its canonical arm terminal")
            for item in group:
                index = item["path_index"]
                candidate = item.get("candidate")
                expected_extended = np.concatenate((
                    expected_syndromes[shot][:22], [index & 1], expected_syndromes[shot][22:], [(index >> 1) & 1],
                )).astype(np.uint8)
                if (not isinstance(candidate, list) or len(candidate) != 46
                        or any(type(value) is not int or not 0 <= value <= 3 for value in candidate)):
                    _fail("aSCED path candidate is absent or not a 46-qubit Pauli vector")
                candidate_array = np.asarray(candidate, dtype=np.uint8)
                observed = pauli_syndrome(batch.h_ext if arm == "asced_ordinary" else overcomplete_checks, candidate_array)
                expected_observed = expected_extended if arm == "asced_ordinary" else np.asarray(
                    (overcomplete.mapping.astype(np.int64) @ expected_extended.astype(np.int64)) % 2, dtype=np.uint8,
                )
                if (item.get("virtual_bits_lsb_first") != [index & 1, (index >> 1) & 1]
                        or len(item.get("extended_syndrome", [])) != 46
                        or item.get("extended_syndrome") != expected_extended.tolist()
                        or item.get("original_syndrome") != expected_syndromes[shot].tolist()
                        or item.get("extended_valid") is not bool(np.array_equal(observed, expected_observed))
                        or item.get("original_valid") is not bool(np.array_equal(original_code.syndrome(candidate_array), expected_syndromes[shot]))
                        or not item.get("work")):
                    _fail("aSCED path does not retain replayable LSB virtual bits, typed syndrome dimensions, or work")
                if arm == "asced_ordinary" and item.get("overcomplete_map_receipt") is not None:
                    _fail("ordinary aSCED path unexpectedly binds an overcomplete map")
                if arm == "asced_overcomplete" and item.get("overcomplete_map_receipt") != _MAP_RECEIPT:
                    _fail("overcomplete aSCED path does not bind the exact constructed map receipt")
    aggregate = native["aggregate"]
    if receipt.get("native_aggregate") != {"trials": aggregate["trials"], "logical_errors": aggregate["logical_errors"], "sample_matching": "unavailable_aggregate_only"}:
        _fail("native aggregate facts or qualified unavailable matching claim drifted")
    # Reuse the run path so candidates, terminals, work, selections, and paths
    # are compared to executable controller output rather than self-reported
    # event fields.
    with tempfile.TemporaryDirectory(prefix="phase10-replay-", dir=output.parent) as temporary:
        expected_output = Path(temporary) / "expected"
        run(study_path, native_path, expected_output)
        if ledger.read_bytes() != (expected_output / "canonical-ledger.jsonl").read_bytes():
            _fail("canonical ledger differs from full deterministic decoder replay")
        if receipt_path.read_bytes() != (expected_output / "study-receipt.json").read_bytes():
            _fail("study receipt differs from full deterministic decoder replay")
    print(json.dumps({"verified": True, "canonical_terminals": len(terminals), "asced_paths": len(paths), "native_trials": aggregate["trials"], "native_logical_errors": aggregate["logical_errors"]}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "verify"))
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--native-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", action="store_true", help="regenerate all 256 canonical shots before declaring decoder output verified")
    args = parser.parse_args()
    try:
        if args.command == "freeze":
            _validate(args.study, args.native_receipt); print(json.dumps({"frozen": True, "study": str(args.study)}, sort_keys=True))
        elif args.command == "run":
            if args.output is None: _fail("run requires --output")
            run(args.study, args.native_receipt, args.output)
        else:
            if args.output is None: _fail("verify requires --output")
            verify(args.study, args.native_receipt, args.output, replay=args.replay)
    except (ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__":
    main()
