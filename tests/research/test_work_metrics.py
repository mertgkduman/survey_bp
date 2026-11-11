"""Retained work counters preserve component and directed-update semantics."""

import csv
import json
from pathlib import Path

import pytest

from bp_registry.research.catalog import _iteration_work, build_catalog
from bp_registry.research.results import _work_columns


ROOT = Path(__file__).resolve().parents[2]


def test_unequal_binary_graphs_require_component_counters(monkeypatch):
    monkeypatch.setattr("bp_registry.research.catalog._css_edge_counts", lambda *args: (8, 4))
    binary = _iteration_work(ROOT, "example", 10, joint=False, components=2)
    assert binary["mean_iterations"] == 10
    assert binary["mean_directed_edge_updates"] is None
    assert _iteration_work(ROOT, "example", 10, joint=True)["mean_directed_edge_updates"] == 240
    assert _iteration_work(ROOT, "example", 10, joint=False)["mean_directed_edge_updates"] == 80


def test_retained_cross_code_and_completion_work_uses_all_component_sweeps():
    catalog = build_catalog(ROOT)
    points = {(s["dataset_id"], s["code_id"], s["source_decoder_id"]): s["points"]
              for s in catalog["result_series"]}
    source = ROOT / "data/reproductions/yao-2312-10950-cross-code/depolarizing/results/all_depolarizing.csv"
    with source.open() as stream:
        for row in csv.DictReader(stream):
            key = ("yao-cross-code-depolarizing", row["code"], row["decoder"])
            point = next(p for p in points[key] if p["x"] == float(row["p"]))
            components = 2 if row["decoder"].startswith("binary") else 1
            assert point["mean_iterations"] == pytest.approx(components * float(row["mean_iterations_per_component"]))
            assert point["mean_directed_edge_updates"] == float(row["mean_directed_edge_updates"])
            assert point["mean_work"] == point["mean_directed_edge_updates"]

    for (dataset, code, arm), rows in points.items():
        if dataset != "yao-bpgd-completion":
            continue
        matrices = json.loads((ROOT / f"web/research/inputs/{code}.json").read_text())
        edges = sum(sum(row) for row in matrices["hz"])
        if arm == "qbp":
            edges += sum(sum(row) for row in matrices["hx"])
        for point in rows:
            assert point["mean_iterations"] == point["mean_work"]
            assert point["mean_directed_edge_updates"] == pytest.approx(2 * edges * point["mean_iterations"])


def test_portable_unequal_graphs_use_each_retained_component_counter(tmp_path):
    rows = [{"rate_index": 0, "mean_iterations": 8.5, "n": 2}]
    spec = {"decoder": {"family": "binary_css"}, "problem": {"code": {
        "kind": "embedded_css", "hx": [[1] * 4, [1] * 4], "hz": [[1] * 4]}}}
    events = [{"kind": "shot", "rate_index": 0, "family": "binary_css", "outcome": "exact",
               "iterations": {"x": x, "z": z}} for x, z in ((2, 5), (3, 7))]
    (tmp_path / "events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events))
    work = _work_columns(tmp_path, spec, rows)[0]
    assert work["mean_iterations"] == 8.5
    assert work["mean_directed_edge_updates"] == 116
    assert work["iteration_unit"] == "component sweeps"
