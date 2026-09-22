"""Contracts for strict executable manifests and preflight."""

import pytest


def test_manifest_rejects_unknown_fields():
    from bp_registry.manifests import Manifest

    with pytest.raises((ValueError, TypeError)):
        Manifest.model_validate({"schema_version": 1, "unknown_key": "ignored"})


def test_manifest_rejects_missing_required_fields():
    from bp_registry.manifests import Manifest

    with pytest.raises((ValueError, TypeError)):
        Manifest.model_validate({"schema_version": 1})


def test_preflight_rejects_missing_artifact_before_native_call(tmp_path, monkeypatch):
    from bp_registry import manifests, reference

    def forbidden_decode(*args, **kwargs):
        raise AssertionError("native decoder reached before preflight")

    monkeypatch.setattr(reference, "decode", forbidden_decode)
    with pytest.raises((ValueError, FileNotFoundError)):
        manifests.preflight({"schema_version": 1, "artifact_path": str(tmp_path / "missing.json")})

