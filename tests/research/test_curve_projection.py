"""Conservative browser-side evidence projection semantics."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="curve projection runs in the browser")


def project(catalog):
    script = """require('./web/research/curve-projection.js');const input=JSON.parse(process.argv[1]);const display=new Map(input.result_series.map(s=>[s.series_id,{label:'Q-BP, SP, T = 10',algorithm:'Q-BP',rule:'SP',precision:'float64',parameters:[],retired:null}]));console.log(JSON.stringify(ResearchCurves.project(input,display)));"""
    return json.loads(subprocess.check_output(["node", "-e", script, json.dumps(catalog)], cwd=ROOT, text=True))


def catalog(series, decoders=None):
    return {"datasets": [{"dataset_id": "d", "evidence_status": "canonical_adaptation"}], "result_series": series,
            "decoders": decoders or []}


def row(identifier, *, seed, evidence, failures=1, shots=10, pool=False):
    metadata = {"seed": seed, "source_evidence_path": evidence,
                "denominator_definition": "all terminal shots", "pooling_contract": "independent_fixed_iid_disjoint_v1" if pool else None}
    return {"series_id": identifier, "dataset_id": "d", "code_id": "a5", "decoder_id": identifier,
            "channel_kind": "depolarizing", "label": identifier,
            "points": [{"x": .06, "y": failures / shots, "n": shots, "failures": failures,
                        "ci_low": .01, "ci_high": .3, "status": "complete", "metadata": metadata}]}


def test_same_retained_evidence_is_deduplicated_without_adding_counts():
    curves = project(catalog([row("a", seed=1, evidence="one.json"), row("b", seed=1, evidence="one.json")]))
    assert len(curves) == 1
    point = curves[0]["points"][0]
    assert point["n"] == 10 and point["failures"] == 1
    assert point["provenance_members"] and len(point["provenance_members"]) == 2
    assert curves[0]["projection"]["method"] == "deduplicated_reused_evidence"


def test_unbound_or_overlapping_evidence_stays_as_separate_unpooled_points_in_one_view():
    curves = project(catalog([row("a", seed=1, evidence=""), row("b", seed=2, evidence="")]))
    assert len(curves) == 1
    assert len(curves[0]["points"]) == 2
    assert all(point["n"] == 10 for point in curves[0]["points"])
    assert curves[0]["projection"]["method"] == "single_retained_measurement"


def test_explicit_disjoint_fixed_iid_contract_pools_and_recomputes_interval():
    curves = project(catalog(
        [row("a", seed=1, evidence="a.json", failures=1, pool=True), row("b", seed=2, evidence="b.json", failures=2, pool=True)],
        [
            {"decoder_id": "a", "configuration": {"effective_policy": {"kernel": "known", "check_cap": None}}},
            {"decoder_id": "b", "configuration": {"effective_policy": {"kernel": "known", "check_cap": None}}},
        ],
    ))
    assert len(curves) == 1
    point = curves[0]["points"][0]
    assert point["n"] == 20 and point["failures"] == 3 and point["y"] == .15
    assert point["ci_low"] != .01 and point["ci_high"] != .3
    assert curves[0]["projection"]["method"] == "pooled_independent_fixed_iid"


def test_multiple_rates_and_seed_cohorts_share_one_unique_curve_identity():
    first = row("a", seed=1, evidence="a.json")
    first["points"].append({**first["points"][0], "x": .08, "metadata": {**first["points"][0]["metadata"], "source_evidence_path": "a-08.json"}})
    second = row("b", seed=2, evidence="b.json")
    curves = project(catalog([first, second]))
    assert len(curves) == 1
    assert curves[0]["series_id"] == curves[0]["curve_id"]
    assert len({point["x"] for point in curves[0]["points"]}) == 2
    assert len(curves[0]["points"]) == 3


def test_only_distinct_sampling_roles_get_a_brief_evidence_qualifier():
    pilot = row("pilot", seed=1, evidence="pilot.json")
    pilot["points"][0]["metadata"]["cohort_kind"] = "pilot"
    campaign = row("campaign", seed=2, evidence="campaign.json")
    campaign["points"][0]["metadata"]["cohort_kind"] = "bounded_campaign"
    curves = project(catalog([pilot, campaign]))
    assert {curve["label"].rsplit(", ", 1)[-1] for curve in curves} == {"pilot", "bounded campaign"}
    assert all("seed" not in curve["label"] and "N =" not in curve["label"] for curve in curves)


def test_same_display_name_with_distinct_effective_kernels_stays_separate():
    curves = project(catalog(
        [row("a", seed=1, evidence="a.json", pool=True), row("b", seed=2, evidence="b.json", pool=True)],
        [
            {"decoder_id": "a", "configuration": {"effective_policy": {"kernel": "v1", "check_cap": 25}}},
            {"decoder_id": "b", "configuration": {"effective_policy": {"kernel": "v2", "check_cap": None}}},
        ],
    ))
    assert len(curves) == 2
    assert {curve["implementation_identity"] for curve in curves} == {
        '{"check_cap":25,"kernel":"v1"}', '{"check_cap":null,"kernel":"v2"}',
    }


def test_unknown_implementation_never_pools_even_with_a_cohort_disjointness_marker():
    curves = project(catalog([row("a", seed=1, evidence="a.json", pool=True),
                              row("b", seed=2, evidence="b.json", pool=True)]))
    assert len(curves) == 1
    assert len(curves[0]["points"]) == 2
    assert all(p["n"] == 10 for p in curves[0]["points"])


def test_adding_a_cohort_preserves_the_curve_view_identity():
    first = row("a", seed=1, evidence="a.json")
    before = project(catalog([first]))[0]
    after = project(catalog([first, row("b", seed=2, evidence="b.json")]))[0]
    assert before["curve_id"] == after["curve_id"]
    assert after["projection"]["source_series_ids"] == ["a", "b"]
