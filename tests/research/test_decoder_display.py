"""Scientific display labels never replace stored specs or conflate retired clipping with quantization."""
import json
from pathlib import Path
import subprocess
import shutil
import pytest

pytestmark=pytest.mark.skipif(shutil.which("node") is None, reason="JavaScript formatter checks require Node; the browser verification also covers them")

ROOT=Path(__file__).resolve().parents[2]


def display():
    code="""require('./web/research/decoder-display.js');const c=require('./web/research/catalog.json');const labels=DecoderDisplay.labels(c);console.log(JSON.stringify(c.result_series.map(s=>({...s,display:labels.get(s.series_id)}))));"""
    return json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT,text=True))


def test_retired_global_clipping_is_hidden_but_corrected_quantization_remains():
    rows=display()
    for row in rows:
        if row['dataset_id']=='yao-vanilla-a5-b2':
            assert bool(row['display']['retired']) == (row['source_decoder_id'] in {'bp4_v1','binary_v1'})
        if row['dataset_id']=='pfister-presentation-ms-both-changes':
            assert row['display']['retired'] is None
            assert 's = 16' in row['display']['label']
        if row['dataset_id']=='pfister-presentation-full-v2-curves':
            assert bool(row['display']['retired']) == (row['source_decoder_id']=='bp4_vanilla_ms_q8')


def test_names_use_recorded_parameters_and_selected_arm_overrides():
    rows=display()
    curve=next(s for s in rows if s['dataset_id']=='pfister-presentation-full-v2-curves' and s['code_id']=='b1' and s['source_decoder_id']=='bp4_tuned_sp_v2')
    label=curve['display']['label']
    assert label.startswith('Q-BP, SP') and 'd = 0.1' in label and 'T = 1000' in label
    assert 'precision = float64' in label and 'c = none' in label
    for row in rows:
        if row['dataset_id'].startswith('yao-tuned-qbpgd') and row['code_id']=='a5':
            assert ('p₀ = 0.005' if row['source_decoder_id']=='tuned' else 'p₀ = 0.06') in row['display']['label']
            assert 'N =' not in row['display']['label']


def test_paper_specific_caps_and_current_circuit_adapter_are_not_retired():
    rows=display()
    assert all(not row['display']['retired'] for row in rows if row['dataset_id'] in {'yao-non-osd-results','bb72-fair-beam-relay-v2','bb72-bpsf-factorial-v2'})
    script="""require('./web/research/decoder-display.js');const request={decoder:{family:'circuit_dem_bp',numerical_profile:'binary-spa-flooding-f64-v1',rule:'spa',max_iterations:10},rate_points:[{label:'fixture'}],budgets:{max_iterations:10},channel:{kind:'embedded_circuit'}};console.log(JSON.stringify(DecoderDisplay.describe({configuration:{experiment:request}})));"""
    value=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
    assert value['retired'] is None
    assert value['label'].startswith('Detector BP')


def test_noise_models_are_explicit_when_same_code_has_different_experiments():
    rows=display()
    for row in rows:
        if row['code_id']=='b1' and row['source_decoder_id']=='qbp_v2':
            if row['dataset_id']=='yao-cross-code-depolarizing':assert 'noise = depolarizing' in row['display']['label']
            if row['dataset_id']=='yao-cross-code-plain-baselines':assert 'noise = X-only' in row['display']['label']


def test_binary_marginal_prior_and_joint_prior_have_distinct_symbols():
    rows=display()
    binary=next(s for s in rows if s['dataset_id']=='yao-cross-code-depolarizing' and s['source_decoder_id']=='binary_v2')
    joint=next(s for s in rows if s['dataset_id']=='yao-cross-code-depolarizing' and s['source_decoder_id']=='qbp_v2')
    assert 'p₀ = 2p/3' in binary['display']['label']
    assert 'p₀ = p' in joint['display']['label']
    for s in rows:
        if s['dataset_id']=='yao-non-osd-results' and s['source_decoder_id']=='qbp':
            assert s['display']['algorithm']=='Q-BP' and 'p₀ = p' in s['display']['label']
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text())
    for d in catalog['decoders']:
        if 'yao-non-osd-results:' in d['decoder_id'] and ':qbp' in d['decoder_id']:
            assert d['configuration']['settings_status']=='inherited_vanilla_policy_file'
            assert d['configuration']['source_path'].endswith('vanilla/decoders/bp4_v2.json')


def test_completion_decoder_labels_show_the_frozen_round_and_iteration_caps():
    script = """require('./web/research/decoder-display.js');
const plan=require('./data/reproductions/yao-2312-10950-bpgd-completion/plan.json');
console.log(JSON.stringify(Object.fromEntries(Object.entries(plan.arms).map(([id, settings]) =>
  [id, DecoderDisplay.describe({configuration:{effective_configuration:settings}}).label]))));"""
    labels = json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))
    assert "BPGD, SP" in labels["b1:bpgd_t100_r882"]
    assert "Tᵣ = 100, R = 882" in labels["b1:bpgd_t100_r882"]
    assert "Tᵣ = 10, R = 1922" in labels["c2:bpgd_t10_r1922"]
    assert "noise = X-only" in labels["c2:bpgd_t10_r1922"]
    for code, limit in (("b1", 88200), ("c2", 19220)):
        label = labels[f"{code}:qbp"]
        assert label.startswith("Q-BP, SP") and f"T = {limit}" in label
        assert "d = 0.1" in label and "noise = depolarizing" in label


def test_unicycle_branch_controller_is_distinct_from_guided_decimation():
    script = """require('./web/research/decoder-display.js');require('./web/research/curve-projection.js');
const plan=require('./data/reproductions/mackay-0304161-unicycle/plan.json');
const decoders=Object.entries(plan.arms).map(([id,settings])=>({decoder_id:id,configuration:{effective_configuration:settings}}));
const series=decoders.map(d=>({series_id:d.decoder_id,decoder_id:d.decoder_id,dataset_id:'u',code_id:'unicycle74',channel_kind:plan.arms[d.decoder_id].noise_model,
points:[.04,.05].map(x=>({x,y:.1,n:100,failures:10,ci_low:.04,ci_high:.2,status:'complete',metadata:{denominator_definition:'quantum block failure'}}))}));
const c={decoders,result_series:series,codes:[{code_id:'unicycle74'}],circuits:[],datasets:[{dataset_id:'u',evidence_status:'controlled_local_baseline'}]};
const labels=DecoderDisplay.labels(c);console.log(JSON.stringify({labels:Object.fromEntries([...labels].map(([id,d])=>[id,d.label])),active:ResearchCurves.active(c,labels).curves}));"""
    value = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True))
    assert len(value['active']) == 3
    label = value['labels']['unicycle_sp']
    assert label.startswith('Unicycle BP, SP') and 'Tₕ = 44100' in label and 'H = 2' in label
    assert 'T = 88200' in label and 'noise = X-only' in label
    assert value['labels']['binary_sp'].startswith('Binary BP, SP')
    assert value['labels']['qbp'].startswith('Q-BP, SP')


def test_source_iteration_dependent_min_sum_scale_is_explicit():
    script="""require('./web/research/decoder-display.js');console.log(JSON.stringify(DecoderDisplay.describe({configuration:{effective_configuration:{family:'binary_css',check_rule:'min_sum',message_resolution:'float64',v2c_damping:0,max_iterations:162,alpha_schedule:'1-2**(-iteration)',prior:'p',noise_model:'x_only'}}})));"""
    value=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
    assert 'αₜ = 1 − 2⁻ᵗ' in value['label'] and 'T = 162' in value['label']


def test_inferred_budget_is_distinguished_from_an_explicit_source_setting():
    script="""require('./web/research/decoder-display.js');console.log(JSON.stringify(DecoderDisplay.describe({configuration:{effective_configuration:{family:'binary_css',check_rule:'sum_product',message_resolution:'float64',max_iterations:100,budget_status:'curve_inferred_not_source_specified'}}})));"""
    value=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
    assert 'T = 100' in value['label'] and 'budget = inferred' in value['label']


def test_isolated_separate_decoder_exposes_full_channel_and_marginal_prior():
    script="""require('./web/research/decoder-display.js');const c={family:'binary_css',decoding_scope:'separate_xz',check_rule:'sum_product',v2c_damping:0,check_cap:null,max_iterations:100,prior:'2p/3',noise_model:'depolarizing',message_resolution:'float64',budget_status:'curve_inferred_not_source_specified'};console.log(JSON.stringify(DecoderDisplay.describe({configuration:{effective_configuration:c}})));"""
    row=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
    assert row['algorithm']=='Binary BP (separate X/Z)'
    assert all(x in row['label'] for x in ('d = 0','T = 100','p₀ = 2p/3','noise = depolarizing','budget = inferred'))
    assert row['retired'] is None
