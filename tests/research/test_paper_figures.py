"""Source-scoped paper views preserve the central measured-curve boundary."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from bp_registry.research.catalog_model import apply_paper_view_metadata, extend_catalog, validate_catalog
from bp_registry.research.paper_references import add_paper_references

ROOT = Path(__file__).resolve().parents[2]


def views(catalog):
    script = """
require('./web/research/curve-projection.js');require('./web/research/paper-figures.js');
const c=JSON.parse(require('fs').readFileSync(0,'utf8'));
const display=new Map(c.result_series.map(s=>[s.series_id,{label:s.label,algorithm:s.label,parameters:[]}]));
console.log(JSON.stringify(ResearchFigures.views(c,display)));
"""
    return json.loads(subprocess.check_output(['node', '-e', script], input=json.dumps(catalog), cwd=ROOT, text=True))


def fixture():
    p=lambda x,figure:dict(x=x,y=.1,n=20,failures=2,status='complete',metadata={'source_figure':figure})
    def series(sid,ds,arm,figure):
        return dict(series_id=sid,dataset_id=ds,decoder_id=sid,source_decoder_id=arm,code_id='c',
                    label='BP',channel_kind='x_only',points=[p(.01,figure),p(.02,figure)])
    c={key:[] for key in ('papers','codes','circuits','channels','decoders','datasets','experiments','result_series')}
    c['papers']=[{'paper_id':'paper'},{'paper_id':'unrelated'}]
    c['codes']=[{'code_id':'c','label':'Code C'}]
    c['datasets']=[{'dataset_id':'source','paper_id':'paper','evidence_status':'canonical_adaptation'},
                   {'dataset_id':'import','paper_id':'paper','evidence_status':'canonical_adaptation'},
                   {'dataset_id':'other','paper_id':'unrelated','evidence_status':'canonical_adaptation'}]
    c['result_series']=[series('f3','source','bp','3'),series('f4','source','bp','4'),
                        series('new','import','bp',None),series('foreign','other','bp',None)]
    c['decoders']=[{'decoder_id':s['decoder_id']} for s in c['result_series']]
    c['paper_figures']=[{'figure_id':'fig3','paper_id':'paper','label':'Fig. 3','code_ids':['c'],
                        'note':'Canonical settings.','source_path':'source.json','source_figure':'3',
                        'reproduction_rules':[{'dataset_id':'source','source_decoder_ids':['bp'],'source_figure':'3'}]}]
    return c


def test_figure_scope_precedes_projection_and_keeps_new_imports_additional():
    c=fixture();before=deepcopy(c);f=views(c)[0]
    assert c==before
    assert len(f['curves'])==2
    assert {s['paper_group'] for s in f['curves']}=={'paper','additional'}
    assert {m['series_id'] for s in f['curves'] for m in s['provenance_members']}=={'f3','new'}
    assert len({s['series_id'] for s in f['curves']})==2


def test_source_membership_cannot_make_single_rate_reproduction_qualify():
    c=fixture()
    c['paper_figures'][0]['reference_curves']=[{
        'code_id':'c','channel_kind':'x_only',
        'matches':[{'dataset_id':'source','source_decoder_id':'bp'}],
        'points':[{'x':.01,'y':.1},{'x':.02,'y':.2}],
    }]
    figure=views(c)[0]
    assert figure['reference_curves'][0]['curve_ids']==[
        s['series_id'] for s in figure['curves'] if s['paper_group']=='paper'
    ]
    c['result_series'][0]['points']=c['result_series'][0]['points'][:1]
    figure=views(c)[0]
    assert figure['reference_curves'][0]['curve_ids']==[]
    curves=figure['curves']
    assert all(s['paper_group']=='additional' for s in curves)


def test_same_rate_cohorts_do_not_qualify_and_empty_papers_disappear():
    c=fixture()
    for s in c['result_series']:
        for p in s['points']:p['x']=.01
    assert views(c)==[]


def test_retired_source_cannot_reappear_in_a_figure():
    c=fixture();c['public_retired_dataset_ids']=['source']
    assert {s['paper_group'] for s in views(c)[0]['curves']}=={'additional'}


def test_valid_zero_failure_bounds_still_count_as_measured_rates():
    c=fixture()
    for p in c['result_series'][0]['points']:
        p.update(y=0,failures=0,ci_high=.05,status='upper_bound')
    assert any(s['paper_group']=='paper' for s in views(c)[0]['curves'])


def test_incompatible_imported_policy_cannot_complete_a_reproduction_curve():
    c=fixture();c['result_series'][0]['points']=c['result_series'][0]['points'][:1]
    c['result_series'][2]['points']=c['result_series'][2]['points'][1:]
    assert views(c)==[]


@pytest.mark.parametrize('change,match',[
    (lambda f:f.update(paper_id='missing'),'unresolved paper'),
    (lambda f:f.update(code_ids=['missing']),'unresolved codes'),
    (lambda f:f.update(note=''),'needs note'),
    (lambda f:f.update(reproduction_rules=[{'dataset_id':'other','source_decoder_ids':['bp']}]),'unrelated dataset'),
    (lambda f:f.update(reproduction_rules=[{'dataset_id':'source','source_decoder_ids':[]}]),'explicit decoder arms'),
])
def test_invalid_figure_relationships_fail_catalog_validation(change,match):
    c=fixture();change(c['paper_figures'][0])
    with pytest.raises(ValueError,match=match):validate_catalog(c)


def test_actual_registry_uses_source_figures_without_promoting_unknown_settings():
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text())
    figures=json.loads((ROOT/'research/catalog/paper-figures.json').read_text())['figures']
    catalog['paper_figures']=figures
    validate_catalog(catalog)
    result=views(catalog)
    assert {f['source_figure'] for f in result if f['paper_id']=='yao-2312-10950-v2'}==set('2345678')
    roffe=next(f for f in result if f['figure_id']=='roffe-fig-3')
    baseline=[s for s in roffe['curves'] if s['paper_group']=='paper']
    assert {s['code_id'] for s in baseline}=={'toric9','toric11','toric13','toric15'}
    assert all(s['channel_kind']=='x_only' for s in baseline)
    for f in result:
        if f['figure_id'] in {'mackay-fig-15','lp1054-example-4'}:
            assert all(s['paper_group']=='additional' for s in f['curves'])
    yao3=next(f for f in result if f['figure_id']=='yao-fig-3')
    assert any(m['dataset_id']=='yao-bpgd-completion' for s in yao3['curves'] if s['paper_group']=='paper' for m in s['provenance_members'])


def test_paper_references_are_extracted_from_sources_without_mutating_results():
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text())
    original=deepcopy(catalog)
    for f in catalog['paper_figures']:
        f.pop('reference_curves',None)
    add_paper_references(catalog,ROOT)
    figures={f['figure_id']:f for f in catalog['paper_figures']}
    assert catalog['result_series']==original['result_series']
    assert catalog['experiments']==original['experiments']
    assert catalog['paper_figures']==original['paper_figures']

    def point(figure, arm, x):
        return next(p['y'] for r in figures[figure]['reference_curves']
                    if any(m['source_decoder_id']==arm for m in r['matches'])
                    for p in r['points'] if p['x']==x)

    assert point('yao-fig-3','bpgd_t10_r882',.04)==6e-6
    assert point('yao-fig-4','bpgd_t10_r882',.04)==3.21835e-6
    roffe=figures['roffe-fig-3']['reference_curves']
    assert {r['code_id'] for r in roffe}=={'toric9','toric11','toric13','toric15'}
    assert sum(len(r['points']) for r in roffe)==109
    mackay,=figures['mackay-fig-15']['reference_curves']
    assert mackay['source_kind']=='digitized' and mackay['code_id']=='unicycle274'
    assert mackay['metric']=='Classical block error rate' and len(mackay['points'])==5
    prior=figures['priortilt-figure-1']['reference_curves']
    assert sum(len(r['points']) for r in prior)==39
    relay=figures['relay-priortilt-figure-1']['reference_curves']
    assert relay==[r for r in prior if r['matches'][0]['source_decoder_id']=='priortilt-paper-relay']
    assert 'reference_curves' not in figures['lp1054-example-4']


def test_catalog_rebuild_loads_and_hashes_the_figure_registry(tmp_path):
    c=fixture();figures=c.pop('paper_figures')
    path=tmp_path/'figures.json'
    path.write_text(json.dumps({'schema':'research-paper-figures-v1','figures':figures}))
    result=extend_catalog(c,{'paper_figures_path':'figures.json'},tmp_path)
    assert result['paper_figures']==figures and 'paper_figures' not in c
    assert result['extension_sources'][-1]['path']=='figures.json'
    assert len(result['extension_sources'][-1]['sha256'])==64
    path.write_text(json.dumps({'schema':'unknown','figures':figures}))
    with pytest.raises(ValueError,match='unsupported paper figure'):
        extend_catalog(c,{'paper_figures_path':'figures.json'},tmp_path)


def test_paper_views_use_guest_caption_and_preserve_evidence_scope():
    catalog = fixture()
    figure = catalog["paper_figures"][0]
    guest = deepcopy(figure)
    guest.update(figure_id="guest", paper_id="unrelated", guest_paper_id="paper",
                 guest_rules=guest["reproduction_rules"], reproduction_rules=[])
    catalog["paper_figures"].append(guest)
    caption = {"figure_number": "4", "quote": "Source caption"}
    coverage = {"summary": "Partial coverage.", "remaining_experiments": ["Run the baseline."]}
    apply_paper_view_metadata(catalog, {
        "paper_views": {"unrelated": {"title": "Full paper title", "coverage": coverage}},
        "source_captions": {"paper": {"3": caption}},
    })
    assert catalog["papers"][1]["title"] == "Full paper title"
    assert catalog["papers"][1]["coverage"] == coverage
    assert all(entry["source_figure"] == "3" for entry in catalog["paper_figures"])
    assert all(entry["label"] == 'Figure 4 "Source caption"' for entry in catalog["paper_figures"])
    assert all(entry["source_caption"] == caption for entry in catalog["paper_figures"])
    validate_catalog(catalog)


def test_missing_comparison_context_does_not_invent_a_runnable_recipe(tmp_path):
    c=fixture();result=extend_catalog(c,{},tmp_path)
    assert {d for e in result['experiments'] for d in e['dataset_ids']}=={'source','import','other'}
    assert all(e['reproduction_recipe']['kind']=='retained_source_only'
               and e['reproduction_recipe']['commands']==[] for e in result['experiments'])
    assert not c['experiments']
    assert extend_catalog(result,{},tmp_path)['experiments']==result['experiments']
