"""Evidence contracts for the isolated aSCED native-reference proposal."""

from __future__ import annotations

import importlib.util
import json
from hashlib import sha256
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "qualify_phase10_native_asced.py"
SPEC = ROOT / "data" / "native" / "phase10-asced-source-spec.json"
RUN_RECEIPT = ROOT / "data" / "native" / "phase10-asced-run-receipt.json"
PHASE10_GATE = ROOT / "scripts" / "run_phase10_quaternary_gate.py"
PHASE10_STUDY = ROOT / "data" / "studies" / "phase10-quaternary-b1-gate.json"
BP4_MANIFEST = ROOT / "data" / "manifests" / "quaternary-gb46-bp4.json"
ASCED_MANIFEST = ROOT / "data" / "manifests" / "quaternary-gb46-asced.json"
PHASE10_OUTPUT = ROOT / "data" / "results" / "phase10-quaternary-b1-gate"


def test_source_identity_records_exact_commit_and_audited_discrepancies() -> None:
    """Freeze the only admissible native identity and every source discrepancy."""
    assert SCRIPT.exists(), "the read-only aSCED qualification command is required"
    assert SPEC.exists(), "the digest-bound aSCED source specification is required"
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["source"]["repository"] == "https://github.com/kit-cel/quantum_asced.git"
    assert spec["source"]["commit"] == "816772071486615dfc7d71d1e15df597edc58a26"
    assert len(spec["source"]["source_digests"]) >= 8
    assert set(spec["discrepancies"]) == {
        "pybind11_gitlink", "demo_path", "license", "pauli_translation",
        "selection", "channel", "instrumentation",
    }
    assert spec["discrepancies"]["license"]["status"] == "unresolved"
    assert spec["discrepancies"]["pauli_translation"]["native"] == ["I", "X", "Z", "Y"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("commit", "main", "exact full 40-character commit"),
        ("repository", "https://github.com/example/substitute.git", "only kit-cel/quantum_asced"),
    ],
)
def test_source_identity_rejects_moving_or_substitute_source(
    tmp_path: Path, field: str, value: str, message: str,
) -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    spec["source"][field] = value
    tampered = tmp_path / "source-spec.json"
    tampered.write_text(json.dumps(spec), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec", str(tampered), "verify-proposal"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert message in result.stderr


def test_digest_discrepancy_and_no_install_guards_are_explicit(tmp_path: Path) -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    spec["source"]["algorithm_files"] = ["missing.cpp"]
    tampered = tmp_path / "source-spec.json"
    tampered.write_text(json.dumps(spec), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec", str(tampered), "verify-proposal"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "algorithm file" in result.stderr
    script_text = SCRIPT.read_text(encoding="utf-8")
    assert "venv.EnvBuilder" in script_text
    assert "--no-deps" in script_text
    assert "commit_api" in script_text


def test_proposal_binds_all_unapproved_packages_overlay_and_cmake_identity() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    proposal = spec["build_proposal"]
    assert proposal is not None, "an inert human-review proposal is required"
    assert proposal["status"] == "pending_human"
    assert set(proposal["python_packages"]) == {
        "numpy", "galois", "matplotlib", "scikit-build-core", "pybind11",
    }
    for lock in proposal["python_packages"].values():
        assert lock["classification"] == "SUS"
        assert lock["registry_url"].startswith("https://pypi.org/pypi/")
        assert len(lock["sha256"]) == 64
    assert proposal["pybind11_overlay"]["commit"] == "97bf890db679505a14dfe547a5e77bb2bd05dc90"
    cmake = proposal["cmake"]
    assert cmake["provider"] == "Kitware"
    assert cmake["ambient_path_fallback"] == "forbidden"
    assert cmake["executable"].startswith(proposal["disposable_root"] + "/")
    assert len(cmake["artifact_sha256"]) == len(cmake["executable_sha256"]) == 64
    assert proposal["algorithm_guard"]["allow_algorithm_modification"] is False


def test_build_refuses_missing_approval_and_ambient_cmake(tmp_path: Path) -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT), "build", "--approval-summary", str(tmp_path / "missing-summary.md"),
            "--receipt", str(tmp_path / "missing-approval.json"), "--work-root", str(tmp_path / "native"), "--integration-mode", "development_integration",
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "approval summary" in result.stderr
    spec["build_proposal"]["cmake"]["executable"] = "/usr/bin/cmake"
    tampered = tmp_path / "source-spec.json"
    tampered.write_text(json.dumps(spec), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec", str(tampered), "verify-proposal"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "only the recorded disposable-root CMake executable" in result.stderr


def test_network_build_requires_an_explicit_marker_and_new_unique_work_root(tmp_path: Path) -> None:
    """Normal tests must never download, build, or reuse another integration root."""
    receipt = tmp_path / "build-receipt.json"
    summary = ROOT / ".planning" / "phases" / "10-correlated-quaternary-execution" / "10-14-SUMMARY.md"
    unselected_root = tmp_path / "unselected-native-build"
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT), "build", "--spec", str(SPEC),
            "--approval-summary", str(summary), "--receipt", str(receipt),
            "--work-root", str(unselected_root), "--integration-mode", "development_integration",
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "explicit --integration-network" in result.stderr
    assert not unselected_root.exists()
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT), "build", "--spec", str(SPEC),
            "--approval-summary", str(summary), "--receipt", str(receipt),
            "--work-root", str(tmp_path), "--integration-network", "--integration-mode", "development_integration",
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "new unique directory" in result.stderr


def test_native_pauli_translation_is_bijective_and_native_identity_is_distinct() -> None:
    """The native I/X/Z/Y representation must not be mistaken for canonical I/X/Y/Z."""
    from bp_registry.quaternary.native_asced import NativeAscedIdentity

    identity = NativeAscedIdentity.approved()
    assert identity.canonical_to_native(("I", "X", "Y", "Z")) == ("I", "X", "Z", "Y")
    assert identity.native_to_canonical(("I", "X", "Z", "Y")) == ("I", "X", "Y", "Z")
    assert identity.source_commit == "816772071486615dfc7d71d1e15df597edc58a26"


def test_native_run_receipt_preserves_aggregate_and_qualified_missingness() -> None:
    """A successful aggregate terminal remains native, bounded, and not assessed."""
    from bp_registry.quaternary.native_asced import run_native_asced_reference

    result = run_native_asced_reference(RUN_RECEIPT, spec_path=SPEC)
    assert result.trials > 0
    assert 0 <= result.logical_errors <= result.trials
    assert result.assessment == "not_assessed"
    assert result.metric("native_shot_identity").missingness.value == "unavailable"
    assert result.metric("native_edge_updates").value is None


@pytest.mark.parametrize(
    ("path", "mutate", "message"),
    [
        ("run", lambda receipt: receipt["aggregate"].update({"logical_errors": 161}), "outside the actual denominator"),
        ("run", lambda receipt: receipt.update({"build_receipt_sha256": "0" * 64}), "does not bind the actual build receipt"),
        ("build", lambda receipt: next(record for record in receipt["commands"] if "checkout" in record["command"]).update({"returncode": 1}), "required successful"),
    ],
)
def test_native_receipt_rejects_forged_build_chain_or_aggregate(
    tmp_path: Path, path: str, mutate: object, message: str,
) -> None:
    from bp_registry.quaternary.native_asced import verify_native_asced_receipt

    build = json.loads((ROOT / "data/native/phase10-asced-build-receipt.json").read_text(encoding="utf-8"))
    run = json.loads(RUN_RECEIPT.read_text(encoding="utf-8"))
    target = build if path == "build" else run
    assert callable(mutate)
    mutate(target)
    build_path, run_path = tmp_path / "phase10-asced-build-receipt.json", tmp_path / "phase10-asced-run-receipt.json"
    build_path.write_text(json.dumps(build), encoding="utf-8")
    if run["build_receipt_sha256"] != "0" * 64:
        run["build_receipt_sha256"] = sha256(build_path.read_bytes()).hexdigest()
    run_path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        verify_native_asced_receipt(run_path, spec_path=SPEC, build_receipt_path=build_path)


def test_phase10_evidence_rejects_a_coherent_forged_aggregate_receipt(tmp_path: Path) -> None:
    """Generic structure is insufficient to turn a copied aggregate into evidence."""
    from bp_registry.quaternary.native_asced import (
        admit_phase10_native_asced_evidence,
        verify_native_asced_receipt,
    )

    build_path = tmp_path / "phase10-asced-build-receipt.json"
    run_path = tmp_path / "phase10-asced-run-receipt.json"
    build_path.write_bytes((ROOT / "data/native/phase10-asced-build-receipt.json").read_bytes())
    run = json.loads(RUN_RECEIPT.read_text(encoding="utf-8"))
    run["build_receipt_sha256"] = sha256(build_path.read_bytes()).hexdigest()
    run["aggregate"].update({"logical_errors": 8, "failure_I": 8, "failure_II": 0, "logical_error_rate": 0.05})
    for fact in run["metric_facts"]:
        if fact["metric"] == "native_logical_errors":
            fact["value"] = 8
    run_path.write_text(json.dumps(run), encoding="utf-8")

    # The generic API correctly recognizes internal consistency only.
    assert verify_native_asced_receipt(run_path, spec_path=SPEC, build_receipt_path=build_path)["aggregate"] == run["aggregate"]
    with pytest.raises(ValueError, match="not the endorsed Phase 10 retained observation"):
        admit_phase10_native_asced_evidence(run_path, spec_path=SPEC, build_receipt_path=build_path)


def test_phase10_mechanism_design_freezes_the_exact_canonical_adaptation_pair() -> None:
    """D-13 fixes GB46, p=.05, seed 10, and every shared canonical sample."""
    assert PHASE10_GATE.exists(), "the digest-checked Phase 10 mechanism gate is required"
    assert PHASE10_STUDY.exists() and BP4_MANIFEST.exists() and ASCED_MANIFEST.exists()
    study = json.loads(PHASE10_STUDY.read_text(encoding="utf-8"))
    bp4 = json.loads(BP4_MANIFEST.read_text(encoding="utf-8"))
    asced = json.loads(ASCED_MANIFEST.read_text(encoding="utf-8"))
    assert study["profile"] == {"code": "GB46", "physical_error_rate": 0.05, "canonical_seed": 10}
    assert study["admitted_shot_ids"] == list(range(256))
    assert study["assessment"] == "not_assessed"
    assert study["phase11_boundary"] == "no_curve_reproduction_or_performance_ranking"
    assert bp4["run_fidelity"] == "canonical_adaptation"
    assert asced["run_fidelity"] == "canonical_adaptation"
    assert asced["ordinary"]["iteration_cap"] == 25
    assert asced["overcomplete"]["iteration_cap"] == 12
    assert asced["ordinary"]["paths_per_shot"] == asced["overcomplete"]["paths_per_shot"] == 4
    pair = asced["constructed_receipt_pair"]
    assert pair["row_order"] == ["H_X", "T_X", "H_Z", "T_Z"]
    assert pair["constructed_splitter_receipt_sha256"] == "d28362b1d8b97eb01768d8fd33c7f6d04c1050ad828b767c5ebb089da59c8fc9"
    assert pair["constructed_map_receipt_sha256"] == "9f40262f7afe0f109759871179b86b369f42711bd607248f87461db7dc2a4177"
    assert study["native_requirement"]["required_terminal"] == "native_success"


def test_phase10_gate_rejects_design_and_native_receipt_tampering(tmp_path: Path) -> None:
    """The study cannot silently drift or accept a failed native substitute."""
    study = json.loads(PHASE10_STUDY.read_text(encoding="utf-8"))
    study["profile"]["physical_error_rate"] = 0.1
    tampered_study = tmp_path / "study.json"
    tampered_study.write_text(json.dumps(study), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(PHASE10_GATE), "freeze", "--study", str(tampered_study), "--native-receipt", str(RUN_RECEIPT)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "p=0.05" in result.stderr

    native = json.loads(RUN_RECEIPT.read_text(encoding="utf-8"))
    native["terminal"] = "native_failed"
    tampered_native = tmp_path / "native.json"
    tampered_native.write_text(json.dumps(native), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(PHASE10_GATE), "freeze", "--study", str(PHASE10_STUDY), "--native-receipt", str(tampered_native)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "native aSCED terminal" in result.stderr


def test_phase10_persisted_evidence_requires_explicit_full_decoder_replay() -> None:
    """Hashes and syndrome checks cannot certify that a decoder made the result."""
    assert (PHASE10_OUTPUT / "canonical-ledger.jsonl").is_file()
    assert (PHASE10_OUTPUT / "study-receipt.json").is_file()
    result = subprocess.run(
        [
            sys.executable, str(PHASE10_GATE), "verify", "--study", str(PHASE10_STUDY),
            "--native-receipt", str(RUN_RECEIPT), "--output", str(PHASE10_OUTPUT),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "requires explicit --replay" in result.stderr


def test_phase10_replay_compares_regenerated_decoder_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    """A syntactically valid submitted ledger still needs executable replay bytes."""
    spec = importlib.util.spec_from_file_location("phase10_gate", PHASE10_GATE)
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    def forged_replay(_study: Path, _native: Path, output: Path) -> None:
        output.mkdir(parents=True)
        (output / "canonical-ledger.jsonl").write_text("forged\n", encoding="utf-8")

    monkeypatch.setattr(gate, "run", forged_replay)
    with pytest.raises(ValueError, match="differs from full deterministic decoder replay"):
        gate.verify(PHASE10_STUDY, RUN_RECEIPT, PHASE10_OUTPUT, replay=True)


def test_phase10_verifier_rejects_tampered_event_identity(tmp_path: Path) -> None:
    """A persisted event ID must bind its exact payload rather than only its count."""
    copied = tmp_path / "result"
    shutil.copytree(PHASE10_OUTPUT, copied)
    ledger = copied / "canonical-ledger.jsonl"
    first, *remaining = ledger.read_text(encoding="utf-8").splitlines()
    event = json.loads(first)
    event["event_id"] = "phase10-tampered"
    ledger.write_text("\n".join([json.dumps(event, sort_keys=True), *remaining]) + "\n", encoding="utf-8")
    receipt = copied / "study-receipt.json"
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_payload["canonical_ledger_sha256"] = sha256(ledger.read_bytes()).hexdigest()
    receipt.write_text(json.dumps(receipt_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PHASE10_GATE), "verify", "--study", str(PHASE10_STUDY),
            "--native-receipt", str(RUN_RECEIPT), "--output", str(copied),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "ledger event identity" in result.stderr
