"""Independent summary arithmetic and budget-locked pointwise comparisons."""
from collections import Counter
import csv
import gzip
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path

from scipy.stats import beta

REPO=Path(__file__).resolve().parents[3]
Q=Path(__file__).resolve().parent
INITIAL=REPO/'data/reproductions/roffe-2005-07016-search'
FRONTIER=INITIAL.with_name('roffe-2005-07016-search-frontier')
OSD=INITIAL.with_name('roffe-2005-07016-osd-fast')
spec=importlib.util.spec_from_file_location('_frontier_result_arithmetic',FRONTIER/'run.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


def digest(path):return sha256(path.read_bytes()).hexdigest()


def load_checked(root):
    plan=run.rt.load(root)
    with gzip.open(root/'verified.json.gz','rt') as stream:v=json.load(stream)
    assert v['plan_sha256']==digest(root/'plan.json')
    source={j['id']:j for j in plan['jobs']}
    for row in v['points']:
        j=row['job'];n=row['shots'];k=row['failures'];counts=row['counts']
        assert j['seed']==plan['protocol']['seeds']['confirmation']
        assert row['point'] in v['finished_strata'] and row['point'] in source
        assert j['decoder']['noise_model']=='x_only' and j['decoder']['search']==j['controls']
        assert sum(counts.values())==n and counts['type_i']+counts['type_ii']==k
        assert k==j['target_block_failures'] or n==j['max_shots']
        assert row['rate']==k/n
        low=0. if k==0 else float(beta.ppf(.025,k,n-k+1))
        high=1. if k==n else float(beta.ppf(.975,k if k==j['target_block_failures'] else k+1,n-k))
        assert math.isclose(low,row['ci95_low'],abs_tol=1e-16)
        assert math.isclose(high,row['ci95_high'],abs_tol=1e-16)
        assert row['runtime_ratio']==row['decode_ns']/row['reference_ns']
        assert 0<=row['directed_edge_updates']<=2*j['graph_edges']*row['iterations']
        directory=REPO/row['directory'];stored=json.loads((directory/'summary.json').read_text())
        assert digest(directory/'summary.json')==row['summary_sha256']
        assert all(row.get(key)==value for key,value in stored.items())
        manifest=json.loads((directory/'manifest.json').read_text())
        assert manifest['job']==j and manifest['campaign_plan_sha256']==v['plan_sha256']
        selection_path=directory.parents[1]/'selection.json'
        assert digest(selection_path)==row['selection_sha256']==manifest['selection_sha256']
        selected=json.loads(selection_path.read_text())
        for budget in row['budgets']:
            finalists=selected['finalists'];eligible=[f for f in finalists if f['runtime_ratio']<=1.1*budget]
            key=lambda f:(f['failures']/f['shots'],f['iterations']/f['shots'],f['runtime_ratio'],run.r.identity(f['controls']))
            winner=min(eligible,key=key) if eligible else min(finalists,key=lambda f:(f['runtime_ratio'],*key(f)))
            assert winner['controls']==j['controls']
    return plan,v


def index(v):
    result={}
    for row in v['points']:
        j=row['job']
        for budget in row['budgets']:
            key=(j['code'],j['physical_p'],j['method'],budget)
            assert key not in result;result[key]=row
    assert len(result)==4*len(v['finished_strata'])
    return result


def main():
    initial_plan,initial=load_checked(INITIAL);plan,new=load_checked(FRONTIER)
    assert new['parent_full_audit_sha256']==digest(INITIAL/'verified.json.gz')
    run.rt.load(OSD);osd=json.loads((OSD/'verified.json').read_text())
    assert osd['plan_sha256']==digest(OSD/'plan.json')
    refs={(r['code'],r['physical_p']):r for r in osd['points'] if r['arm']=='bp_osd0'}
    old_index=index(initial);new_index=index(new);rows=[]
    for (code,p,method,budget),row in sorted(new_index.items()):
        j=row['job'];n=row['shots'];ref=refs.get((code,p));old=old_index[code,p,method,budget]
        rows.append({'code':code,'n_qubits':plan['codes'][code]['n'],'p':p,'method':method,'budget':budget,
                     'ler':row['rate'],'ci95_low':row['ci95_low'],'ci95_high':row['ci95_high'],
                     'shots':n,'failures':row['failures'],'actual_runtime_ratio':row['runtime_ratio'],
                     'actual_within_budget110':row['runtime_ratio']<=1.1*budget,
                     'mean_iterations':row['iterations']/n,'mean_directed_edge_updates':row['directed_edge_updates']/n,
                     'mean_us':row['decode_ns']/n/1000,'p95_us':row['latency_quantiles_seconds']['0.95']*1e6,
                     'p99_us':row['latency_quantiles_seconds']['0.99']*1e6,
                     'initial_ler':old['rate'],'initial_actual_runtime_ratio':old['runtime_ratio'],
                     'new_over_initial_ler':row['rate']/old['rate'] if old['rate'] else None,
                     'osd0_ler':ref['rate'] if ref else None,'osd0_ci95_low':ref['ci95_low'] if ref else None,
                     'osd0_ci95_high':ref['ci95_high'] if ref else None,
                     'new_over_osd0_ler':row['rate']/ref['rate'] if ref and ref['rate'] else None,
                     'pointwise_ci_overlap_osd0':row['ci95_high']>=ref['ci95_low'] and ref['ci95_high']>=row['ci95_low'] if ref else None,
                     'controls':json.dumps(j['controls'],sort_keys=True,separators=(',',':')),
                     'source_directory':row['directory'],'summary_sha256':row['summary_sha256']})
    with (Q/'comparisons.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    result={'status':'passed','initial':{'workers':len(initial['finished_strata']),'measurements':len(initial['points']),
                                       'shots':sum(r['shots'] for r in initial['points']),'training_measurements':len(initial['tuning'])},
            'frontier':{'workers':len(new['finished_strata']),'planned_workers':new['planned_strata'],
                        'measurements':len(new['points']),'shots':sum(r['shots'] for r in new['points']),
                        'failures':sum(r['failures'] for r in new['points']),'training_measurements':len(new['tuning'])},
            'summary_rows_independently_checked':len(initial['points'])+len(new['points']),
            'initial_receipt_sha256':digest(INITIAL/'verified.json.gz'),'frontier_receipt_sha256':digest(FRONTIER/'verified.json.gz'),
            'osd_receipt_sha256':digest(OSD/'verified.json'),'budget_summary':{},'examples':[],
            'scope':'Frozen source/software and every published summary/manifest/count/CI/work bound/ratio/selection checked; full-ledger/reference/endpoint audits reused. No new simulations. CI overlap is descriptive, not equivalence or a simultaneous test.'}
    for method in ('beam','relay'):
        for budget in (.5,1.,2.,4.):
            group=[r for r in rows if r['method']==method and r['budget']==budget]
            eligible=[r for r in group if r['actual_within_budget110']]
            comparable=[r for r in eligible if r['osd0_ler'] is not None]
            result['budget_summary'][method+':'+str(budget)]={
                'completed_points':len(group),'actual_within_budget110':len(eligible),'actual_exceeds_budget110':len(group)-len(eligible),
                'osd_comparable':len(comparable),'lower_ler_estimate':sum(r['ler']<r['osd0_ler'] for r in comparable),
                'overlapping_pointwise_CI':sum(r['pointwise_ci_overlap_osd0'] for r in comparable)}
    result['examples']=sorted([r for r in rows if r['p']==.02 and r['budget']==1.],key=lambda r:(r['n_qubits'],r['method']))
    (Q/'assessment.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    lines=['# Beam/RelayBP broader tuning: checked results','',
           f'Initial study: all218 workers fully audited, {result["initial"]["measurements"]} configurations and {result["initial"]["shots"]:,} shots. Broader study: {result["frontier"]["workers"]}/218 completed workers audited, {result["frontier"]["measurements"]} configurations and {result["frontier"]["shots"]:,} fresh shots. Training remains separate.','',
           'The wider beam search gives a useful accuracy/latency tradeoff at p=.02. It is consistent with OSD-0 at the length162 point at current pointwise precision, and is still about3.0x/2.5x worse in LER at lengths242/338 while using less than0.4/0.22 of the same-CPU reference mean time. RelayBP remains less accurate at these examples. This is not a global equivalence or decoder-superiority claim.','',
           'The following configurations were selected on independent finalist training for the1x upper runtime budget. Actual confirmation timing is shown; consuming the entire budget is not assumed. The other budget selections and every exact control are in comparisons.csv and the study report.','',
           '| Length | Method | LER | 95% interval | Mean time / OSD0 | OSD0 LER | New / initial LER |',
           '| ---: | --- | ---: | --- | ---: | ---: | ---: |']
    for row in result['examples']:
        ref=f'{row["osd0_ler"]:.6g}' if row['osd0_ler'] is not None else 'pending'
        lines.append(f'| {row["n_qubits"]} | {row["method"]} | {row["ler"]:.6g} | [{row["ci95_low"]:.6g}, {row["ci95_high"]:.6g}] | {row["actual_runtime_ratio"]:.3f} | {ref} | {row["new_over_initial_ler"]:.3g} |')
    b=result['budget_summary']['beam:1.0'];rr=result['budget_summary']['relay:1.0']
    lines+=['',f'The1x selected configurations meet the actual110% mean-time ceiling at {b["actual_within_budget110"]}/{b["completed_points"]} beam and {rr["actual_within_budget110"]}/{rr["completed_points"]} Relay points. The remaining {b["actual_exceeds_budget110"]+rr["actual_exceeds_budget110"]} are explicitly over budget; they cannot support a strict same-budget claim. Other target bands remain in assessment.json/comparisons.csv. Budget-role rows can refer to the same deduplicated measurement; totals count each fresh configuration once.','',
            'Twenty-failure estimates have broad intervals. Different point-specific controls can produce nonmonotonic estimates across rates; this finite search is not proof of a threshold or optimum. Pointwise interval overlap cannot establish statistical equivalence. Raw runtimes across hosts are not directly comparable; ratios use same-worker contemporaneous warmed OSD-0 references. The missing length450 beam confirmation and OSD-0 reference remain pending.','',
            'All settings retain all-path mean iterations, actual masked directed-edge updates, mean time and1%-bin p50/p95/p99 latency. Initial and broader confirmation seeds are independent and are never pooled. The broader proposal rule uses parent training only; its adaptive design timing is recorded in its frozen README.','',
            '![Accuracy and measured latency](ler-latency.png)','',
            'The full broader-study RESULTS.md/results-table.csv preserves every fresh configuration; comparisons.csv here contains each preselected upper-budget role. Central display eligibility still requires multiple distinct measured error rates for each compatible concrete policy.']
    (Q/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
