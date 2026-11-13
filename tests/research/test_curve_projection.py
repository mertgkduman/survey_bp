"""Conservative browser-side evidence projection semantics."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="curve projection runs in the browser")


def project(catalog):
    script = """require('./web/research/curve-projection.js');const input=JSON.parse(process.argv[1]);const display=new Map(input.result_series.map(s=>[s.series_id,{label:'Q-BP, SP, T = 10',algorithm:'Q-BP',rule:'SP',precision:'float64',parameters:[],retired:null}]));console.log(JSON.stringify(ResearchCurves.projectEvidence(input,display)));"""
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


def active_view(value):
    script = """require('./web/research/decoder-display.js');require('./web/research/curve-projection.js');const c=JSON.parse(require('fs').readFileSync(0,'utf8'));const v=ResearchCurves.active(c,DecoderDisplay.labels(c));console.log(JSON.stringify({...v,decoderIds:[...v.decoderIds]}));"""
    return json.loads(subprocess.check_output(["node", "-e", script], input=json.dumps(value), cwd=ROOT, text=True))


def with_rates(record, rates=(.06, .08)):
    from copy import deepcopy
    result = deepcopy(record)
    result['points'] = [{**deepcopy(record['points'][0]), 'x': p} for p in rates]
    return result


def test_active_single_rate_cohorts_do_not_qualify_even_if_pooled():
    for pool in (False, True):
        c = catalog([row('a', seed=1, evidence='a.json', pool=pool),
                     row('b', seed=2, evidence='b.json', pool=pool)],
                    [{'decoder_id': id, 'configuration': {'effective_policy': {'kernel': 'same'}}} for id in ('a', 'b')])
        assert active_view(c)['curves'] == []


def test_active_filters_after_validity_retirement_and_source_exclusion():
    measured = with_rates(row('a', seed=1, evidence='a.json'))
    for status in ('pending', 'unmeasured', 'source_only'):
        measured['points'][1]['status'] = status
        assert active_view(catalog([measured]))['curves'] == []
    measured['points'][1]['status'] = 'complete'
    measured['points'][1]['y'] = None
    assert active_view(catalog([measured]))['curves'] == []
    measured['points'][1]['y'] = .1
    measured['points'][1]['x'] = None
    assert active_view(catalog([measured]))['curves'] == []
    measured = with_rates(row('a', seed=1, evidence='a.json'))
    c = catalog([measured])
    c['datasets'][0]['evidence_status'] = 'source_transcription'
    assert active_view(c)['curves'] == []
    c = catalog([measured], [{'decoder_id': 'a', 'configuration': {'effective_policy': {
        'schema': 'vanilla-bp-decoder-v1', 'family': 'bp4', 'numerical_profile': 'quaternary-bp4-f64-v1',
        'max_iterations': 10, 'damping_old': 0, 'check_cap': 25}}}])
    assert active_view(c)['curves'] == []


def test_active_zero_failure_bounds_count_as_measured_rates_and_raw_catalog_is_unchanged():
    from copy import deepcopy
    c = catalog([with_rates(row('a', seed=1, evidence='a.json', failures=0))])
    c['codes'] = [{'code_id': 'a5'}, {'code_id': 'empty'}]
    c['circuits'] = [{'circuit_id': 'empty-circuit'}]
    before = deepcopy(c)
    view = active_view(c)
    assert len(view['curves']) == 1
    assert [p['y'] for p in view['curves'][0]['points']] == [0, 0]
    assert view['codes'] == [{'code_id': 'a5'}]
    assert view['circuits'] == []
    assert view['decoderIds'] == ['a']
    assert c == before


@pytest.mark.parametrize('difference', ['channel', 'kernel', 'role', 'evaluator'])
def test_active_incompatible_single_rate_evidence_cannot_create_a_curve(difference):
    a, b = row('a', seed=1, evidence='a.json'), row('b', seed=2, evidence='b.json')
    b['points'][0]['x'] = .08
    decoders = [{'decoder_id': id, 'configuration': {'effective_policy': {'kernel': 'same'}}} for id in ('a', 'b')]
    if difference == 'channel':
        b['channel_kind'] = 'x_only'
    elif difference == 'kernel':
        decoders[1]['configuration']['effective_policy']['kernel'] = 'other'
    elif difference == 'role':
        b['points'][0]['metadata']['cohort_kind'] = 'pilot'
    else:
        b['points'][0]['metadata']['denominator_definition'] = 'other evaluator'
    assert active_view(catalog([a, b], decoders))['curves'] == []


def test_active_compatible_projection_can_qualify_across_source_records():
    a, b = row('a', seed=1, evidence='a.json'), row('b', seed=2, evidence='b.json')
    b['points'][0]['x'] = .08
    c = catalog([a, b], [{'decoder_id': id, 'configuration': {'effective_policy': {'kernel': 'same'}}} for id in ('a', 'b')])
    view = active_view(c)
    assert len(view['curves']) == 1
    assert set(view['decoderIds']) == {'a', 'b'}
    assert len(view['curves'][0]['provenance_members']) == 2


@pytest.mark.parametrize('identifier', ['three-qubit', 'project-three-qubit-css-fixture'])
def test_active_fixture_cannot_return_through_imported_evidence(identifier):
    record = with_rates(row('a', seed=1, evidence='a.json'))
    record['code_id'] = identifier
    c = catalog([record])
    c['codes'] = [{'code_id': identifier}]
    assert active_view(c)['curves'] == []
    assert active_view(c)['codes'] == []


@pytest.mark.parametrize('semantics', ['circuit_setting_index', 'decoder_prior_probability'])
def test_settings_or_prior_sweeps_are_not_multiple_measured_error_rates(semantics):
    record = with_rates(row('a', seed=1, evidence='a.json'))
    for point in record['points']:
        point['metadata']['x_semantics'] = semantics
    assert active_view(catalog([record]))['curves'] == []


def test_rebuilt_catalog_uses_same_active_view_as_browser_and_preserves_retained_evidence():
    from bp_registry.research.catalog import build_catalog
    c = build_catalog(ROOT)
    view = active_view(c)
    legacy = [s for s in view['curves'] if s['dataset_id'] not in {'yao-bpgd-completion', 'mackay-unicycle-bp', 'mackay-unicycle-paper-rates', 'mackay-damping-confirmation', 'roffe-2020-figure3-canonical-bp'}]
    assert len(legacy) == 53
    assert sum(len(s['points']) for s in legacy) == 262
    added = {s['code_id'] for s in view['curves'] if s['dataset_id'] in {'mackay-unicycle-bp', 'mackay-unicycle-paper-rates', 'mackay-damping-confirmation', 'roffe-2020-figure3-canonical-bp'}}
    assert {code['code_id'] for code in view['codes']} == {'a5', 'b2', 'b1', 'c2', 'double-gross', 'bb72'} | added
    assert view['circuits'] == []
    from bp_registry.research.inputs import input_registry
    assert len(c['codes']) == len(input_registry(ROOT)['codes']) and len(c['circuits']) == 3
    assert any(s['code_id'] == 'relay-surface-d3' for s in c['result_series'])
    assert all(len({p['x'] for p in s['points']}) >= 2 for s in view['curves'])


def test_public_dataset_retirement_preserves_raw_evidence_and_hides_all_choices():
    record = with_rates(row('a', seed=1, evidence='retained.json'))
    c = catalog([record])
    c['codes'] = [{'code_id': 'a5'}]
    c['circuits'] = []
    c['public_retired_dataset_ids'] = ['d']
    assert active_view(c)['curves'] == [] and active_view(c)['codes'] == []
    assert c['result_series'][0] == record


def test_nonphysical_coordinates_cannot_join_a_physical_curve():
    record = with_rates(row('a', seed=1, evidence='a.json'))
    record['points'].append({**record['points'][0], 'x': .1,
                             'metadata': {**record['points'][0]['metadata'], 'x_semantics': 'decoder_prior_probability'}})
    curves = active_view(catalog([record]))['curves']
    assert len(curves) == 1
    assert [p['x'] for p in curves[0]['points']] == [.06, .08]


def test_completion_retires_only_the_requested_historical_bounded_bpgd():
    old = {"dataset_id": "yao-non-osd-results", "evidence_status": "canonical_adaptation"}
    b1 = {**row("bounded", seed=1, evidence="old.json"), "dataset_id": old["dataset_id"],
          "code_id": "b1", "source_decoder_id": "bpgd_t100_r882"}
    b1["points"][0]["metadata"]["sampling_method"] = "bounded_campaign"
    importance = {**b1, "series_id": "importance", "points": [
        {**b1["points"][0], "metadata": {"sampling_method": "importance_sampling"}}
    ]}
    other = {**b1, "series_id": "other", "source_decoder_id": "bpgd_random_t100"}
    curves = project({"datasets": [old], "result_series": [b1, importance, other]})
    assert {curve["source_series_id"] for curve in curves} == {"importance", "other"}


def test_pooled_work_averages_use_shot_weights_and_preserve_missing_counters():
    first = row("a", seed=1, evidence="a.json", pool=True)
    second = row("b", seed=2, evidence="b.json", shots=30, pool=True)
    first["points"][0].update(mean_iterations=2, mean_directed_edge_updates=20)
    second["points"][0].update(mean_iterations=6, mean_directed_edge_updates=60)
    decoders = [{"decoder_id": id, "configuration": {"effective_policy": {"kernel": "same"}}}
                for id in ("a", "b")]
    point = project(catalog([first, second], decoders))[0]["points"][0]
    assert point["mean_iterations"] == 5
    assert point["mean_directed_edge_updates"] == 50
    second["points"][0]["mean_directed_edge_updates"] = None
    point = project(catalog([first, second], decoders))[0]["points"][0]
    assert point["mean_directed_edge_updates"] is None
    assert point["mean_iterations"] == 5


def test_variable_min_sum_schedule_cannot_supply_points_to_a_constant_scale_curve():
    # Same concise labels cannot override incompatible effective sweep schedules.
    curves = project(catalog(
        [row('variable', seed=1, evidence='variable.json'), row('constant', seed=2, evidence='constant.json')],
        [
            {'decoder_id': 'variable', 'configuration': {'effective_configuration': {'family': 'binary_css', 'check_rule': 'min_sum', 'alpha_schedule': '1-2**(-iteration)', 'first_iteration': 1}}},
            {'decoder_id': 'constant', 'configuration': {'effective_configuration': {'family': 'binary_css', 'check_rule': 'min_sum', 'alpha_schedule': 'constant', 'first_iteration': 1}}},
        ],
    ))
    assert len(curves) == 2
    assert all(len(curve['points']) == 1 for curve in curves)
