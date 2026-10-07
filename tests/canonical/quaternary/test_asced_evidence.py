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
    assert "pip install" in script_text
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
