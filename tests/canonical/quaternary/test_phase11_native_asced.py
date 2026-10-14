"""Regression coverage for the unapplied Phase 11 native aSCED proposal."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "qualify_phase11_native_asced.py"
SOURCE = Path("/tmp/phase10-asced-native/source/quantum_asced")


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_tracer_current_unavailable_is_read_only_and_aggregate_only() -> None:
    """The retained Phase 10 aggregate cannot become matched-shot evidence."""
    completed = _run("inspect", "--source-dir", str(SOURCE))

    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["matched_input_status"] == "unavailable"
    assert receipt["execution_authorized"] is False
    assert receipt["aggregate_receipt_limits"] == [
        "no_injected_error",
        "no_per_shot_identity",
        "no_paired_outcomes",
        "no_random_seed",
    ]
    assert receipt["observed_source_symbols"] == {
        "internal_sampling": "Simulation_Env::simulate_trial -> channel.simulate_error",
        "unchanged_downstream": "simulate_syndrome_extraction -> decode -> logical/physical evaluation",
        "missing_pybind_entrypoint": "Simulation_Env has no injected-error binding",
    }


def test_current_unavailable_rejects_pinned_source_drift(tmp_path: Path) -> None:
    changed = tmp_path / "Simulation_Env.cpp"
    changed.write_text("drift\n", encoding="utf-8")

    completed = _run("inspect", "--source-dir", str(tmp_path))

    assert completed.returncode != 0
    assert "source digest mismatch" in completed.stderr


def test_proposal_emits_unapplied_diff_with_translation_and_authorization(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    patch = tmp_path / "proposal.patch"
    completed = _run(
        "proposal",
        "--source-dir",
        str(SOURCE),
        "--proposal-path",
        str(proposal),
        "--patch-path",
        str(patch),
    )

    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(proposal.read_text(encoding="utf-8"))
    diff = patch.read_text(encoding="utf-8")
    assert receipt["authorization_required"] is True
    assert receipt["derivative_execution_authorized"] is False
    assert receipt["native_order"] == ["I", "X", "Z", "Y"]
    assert receipt["translation_round_trips"] == [
        {"canonical": ["I", "X", "Y", "Z"], "native": ["I", "X", "Z", "Y"], "round_trip": ["I", "X", "Y", "Z"]},
        {"canonical": ["Y", "Z", "Y", "X"], "native": ["Z", "Y", "Z", "X"], "round_trip": ["Y", "Z", "Y", "X"]},
    ]
    assert receipt["diff_sha256"]
    assert receipt["splitter_randomness_limit"]
    assert "channel.simulate_error" not in receipt["unchanged_downstream_symbols"]
    assert "src/Simulation_Env.cpp" in receipt["touched_files"]
    assert "src/Pybind11_Module.cpp" in receipt["touched_files"]
    assert "+    // Proposal-only entry point: bypasses channel sampling." in diff
    assert "+        .def(\"run_injected_error\"" in diff


def test_diff_scope_is_limited_and_preserves_existing_aggregate_entrypoint(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    patch = tmp_path / "proposal.patch"
    assert _run("proposal", "--source-dir", str(SOURCE), "--proposal-path", str(proposal), "--patch-path", str(patch)).returncode == 0

    receipt = json.loads(proposal.read_text(encoding="utf-8"))
    assert receipt["unchanged_downstream_symbols"] == [
        "channel.simulate_syndrome_extraction",
        "decoder.decode",
        "decoder.syndromes_match",
        "channel.check_logical_equivalence",
        "channel.check_physical_equivalence",
        "Simulation_Env::get_error_rates",
    ]
    assert receipt["forbidden_changes"] == ["algorithm source", "Pauli semantics", "candidate selection", "channel code"]
    assert receipt["proposed_source_identity"] is None
    assert receipt["proposed_build_identity"] is None
    assert receipt["proposed_run_identity"] is None


def test_proposal_checked_in_review_package_is_an_unapplied_validated_derivative() -> None:
    """The repository carries review bytes, never an applied or runnable derivative."""
    completed = _run(
        "verify-proposal",
        "--proposal-path",
        str(ROOT / "data/native/phase11-asced-injected-input-proposal.json"),
        "--patch-path",
        str(ROOT / "data/native/phase11-asced-injected-input-diff.patch"),
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "execution_authorized": False,
        "schema": "phase11-asced-proposal-verification-v1",
        "status": "review_only_valid",
    }


def test_proposal_rejects_tampered_receipt_or_patch(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    patch = tmp_path / "proposal.patch"
    assert _run("proposal", "--source-dir", str(SOURCE), "--proposal-path", str(proposal), "--patch-path", str(patch)).returncode == 0
    proposal.write_text(json.dumps({"schema": "tampered"}), encoding="utf-8")

    completed = _run("verify-proposal", "--proposal-path", str(proposal), "--patch-path", str(patch))

    assert completed.returncode != 0
    assert "unsupported proposal schema" in completed.stderr
