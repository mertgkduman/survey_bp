"""Evidence contracts for the isolated aSCED native-reference proposal."""

from __future__ import annotations

import json
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
            "--receipt", str(tmp_path / "missing-approval.json"),
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


def test_approved_build_emits_a_digest_bound_success_receipt(tmp_path: Path) -> None:
    """The approved proposal must build only through the guarded CLI path."""
    receipt = tmp_path / "build-receipt.json"
    summary = ROOT / ".planning" / "phases" / "10-correlated-quaternary-execution" / "10-14-SUMMARY.md"
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT), "build", "--spec", str(SPEC),
            "--approval-summary", str(summary), "--receipt", str(receipt),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["terminal"] == "build_success"
    assert payload["source_spec_sha256"] == "55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e"
    assert payload["compiler"]["path"]
    assert len(payload["source_declared_transitive_build_input"]["observed_sha256"]) == 64


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
