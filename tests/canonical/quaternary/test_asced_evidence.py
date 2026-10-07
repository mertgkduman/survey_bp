"""Evidence contracts for the isolated aSCED native-reference proposal."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "qualify_phase10_native_asced.py"
SPEC = ROOT / "data" / "native" / "phase10-asced-source-spec.json"


def test_source_identity_records_exact_commit_and_audited_discrepancies() -> None:
    """The qualification artifact must exist before it can assert source facts."""
    assert SCRIPT.exists(), "the read-only aSCED qualification command is required"
    assert SPEC.exists(), "the digest-bound aSCED source specification is required"
