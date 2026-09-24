"""Strict public admission tests for the externally supplied cluster policy."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from dataclasses import replace

import numpy as np
import pytest


def test_public_cluster_artifact_boundary_exists():
    """Cluster policy support begins with an explicit, non-executable artifact gate."""
    assert importlib.util.find_spec("bp_registry.canonical.cluster_schedule") is not None


def _write_exact_artifact(tmp_path):
    root = tmp_path / "author-release"
    root.mkdir()
    q_table = root / "q-table.npy"
    np.save(q_table, np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64))
    q_hash = hashlib.sha256(q_table.read_bytes()).hexdigest()
    compatibility = {
        "graph_sha256": "a" * 64,
        "channel": "code_capacity_x",
        "kernel": "binary_spa",
        "state_encoding": "moradi-state-v1",
        "action_encoding": "moradi-action-v1",
        "tie_breaking": "author-declared-stable-v1",
        "q_table_sha256": q_hash,
        "q_shape": [2, 2],
        "check_count": 2,
    }
    partition = root / "partition.json"
    partition.write_text(json.dumps({
        "format_version": 1,
        "source": {
            "id": "moradi-clustered-rl-s", "uri": "https://example.test/moradi",
            "revision": "author-release-v1", "record_sha256": "b" * 64,
        },
        "compatibility": compatibility,
        "partition": [[1], [0]],
    }, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    from bp_registry.canonical.cluster_schedule import ClusterArtifactSpec

    return ClusterArtifactSpec(
        approved_root=root, q_table_path=q_table.name, partition_path=partition.name,
        q_table_sha256=q_hash, partition_sha256=hashlib.sha256(partition.read_bytes()).hexdigest(),
        source_id="moradi-clustered-rl-s", source_uri="https://example.test/moradi",
        source_revision="author-release-v1", source_record_sha256="b" * 64,
        graph_sha256="a" * 64, channel="code_capacity_x", kernel="binary_spa",
        state_encoding="moradi-state-v1", action_encoding="moradi-action-v1",
        tie_breaking="author-declared-stable-v1", q_shape=(2, 2), check_count=2,
    )


def test_exact_bounded_non_executable_bytes_qualify_without_establishing_source_support(tmp_path):
    from bp_registry.canonical.cluster_schedule import load_cluster_artifact

    result = load_cluster_artifact(_write_exact_artifact(tmp_path))
    assert result.qualified and result.status == "qualified"
    assert result.partition == ((1,), (0,))
    assert result.q_table is not None and result.q_table.dtype == np.float64
    report = result.report()
    assert report["source_support"] == report["reproduction_status"] == "not_established_by_qualification"
    assert report["sch_06_status"].startswith("blocked_")
    assert report["external_training_cost"] == "unknown"


@pytest.mark.parametrize("mutate", [
    lambda root: (root / "q-table.npy").write_bytes(b"not-a-npy-file"),
    lambda root: np.save(root / "q-table.npy", np.asarray([[float("nan"), 1.0], [2.0, 3.0]])),
    lambda root: (root / "partition.json").write_text("{}", encoding="utf-8"),
])
def test_corrupt_or_incompatible_cluster_bytes_fail_closed(tmp_path, mutate):
    from bp_registry.canonical.cluster_schedule import load_cluster_artifact

    spec = _write_exact_artifact(tmp_path)
    mutate(tmp_path / "author-release")
    result = load_cluster_artifact(spec)
    assert result.status == "incompatible" and not result.qualified
    assert result.q_table is None and result.partition is None


def test_missing_cluster_bytes_are_structured_unavailability_not_a_substitute(tmp_path):
    from bp_registry.canonical.cluster_schedule import load_cluster_artifact

    spec = _write_exact_artifact(tmp_path)
    (tmp_path / "author-release" / "q-table.npy").unlink()
    result = load_cluster_artifact(spec)
    assert result.status == "unavailable" and not result.qualified
    assert "unavailable" in result.reason


@pytest.mark.parametrize("writer, expected_reason", [
    (
        lambda path: np.save(path, np.asarray([[object(), object()], [object(), object()]], dtype=object)),
        "primitive",
    ),
    (
        lambda path: np.save(path, np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)),
        "primitive",
    ),
])
def test_primitive_dtype_is_checked_before_untrusted_q_values_are_loaded(tmp_path, writer, expected_reason):
    from bp_registry.canonical.cluster_schedule import load_cluster_artifact

    spec = _write_exact_artifact(tmp_path)
    path = tmp_path / "author-release" / "q-table.npy"
    writer(path)
    result = load_cluster_artifact(replace(spec, q_table_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert result.status == "incompatible" and expected_reason in result.reason


def test_size_and_path_escapes_fail_before_any_cluster_policy_can_run(tmp_path):
    from bp_registry.canonical.cluster_schedule import load_cluster_artifact

    spec = _write_exact_artifact(tmp_path)
    oversized = load_cluster_artifact(replace(spec, max_bytes=128))
    escaped = load_cluster_artifact(replace(spec, q_table_path="../q-table.npy"))
    assert oversized.status == escaped.status == "incompatible"
    assert "size limit" in oversized.reason and "unsupported format" in escaped.reason
