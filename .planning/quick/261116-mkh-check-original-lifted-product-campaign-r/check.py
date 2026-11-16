"""Independent summary reconciliation and scientific comparison, no simulations."""
from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import beta

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO/'data/reproductions/panteleev-2012-04068-lifted-product'
spec = importlib.util.spec_from_file_location('_lp1054_run',ROOT/'run.py')
run = importlib.util.module_from_spec(spec);sys.modules[spec.name]=run;spec.loader.exec_module(run)


def digest(path):return sha256(path.read_bytes()).hexdigest()


def identity(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def order(row):
    n = row['shots']
    return row['failures']/n,row['iterations']/n,row['decode_ns']/n,identity(row['controls'])


def verify():
    plan = run.rt.load(ROOT)
    with gzip.open(ROOT/'verified.json.gz','rt') as f:receipt = json.load(f)
    assert receipt['plan_sha256']==digest(ROOT/'plan.json')
    seen = set();groups = defaultdict(lambda:defaultdict(list));points = []
    for row in [*receipt['points'],*receipt['training']]:
        directory = REPO/row['directory'];manifest = json.loads((directory/'manifest.json').read_text())
        assert row['directory'] not in seen;seen.add(row['directory'])
        assert json.loads((directory/'summary.json').read_text())==row
        assert digest(directory/'manifest.json')==row['manifest_sha256']
        assert manifest['plan_sha256']==receipt['plan_sha256']
        assert manifest['job']==row['job'] and manifest['controls']==row['controls']
        assert manifest['stage']==row['stage'] and manifest['seed']==run.SEEDS[row['stage']]
        counts = row['counts'];n = row['shots'];k = row['failures'];c = row['controls']
        assert set(counts)<= {'success','type_i','type_ii'} and sum(counts.values())==n
        assert k==counts.get('type_i',0)+counts.get('type_ii',0)
        assert 0<=k<=n<=manifest['max_shots'] and row['rate']==k/n
        failure_stop = k==manifest['target_failures']
        assert failure_stop or n==manifest['max_shots']
        assert row['stop_reason']==('target_failures' if failure_stop else 'shot_cap')
        lo = float(beta.ppf(.025,k,n-k+1)) if k else 0.
        hi = float(beta.ppf(.975,k if failure_stop else k+1,n-k)) if k<n else 1.
        assert math.isclose(row['ci95_low'],lo,rel_tol=1e-13,abs_tol=1e-15)
        assert math.isclose(row['ci95_high'],hi,rel_tol=1e-13,abs_tol=1e-15)
        joint = c['family']=='qbp';edges = 7440 if joint else 3720
        assert n<=row['iterations']<=n*c['cap']*(1 if joint else 2)
        assert 0<row['directed_edge_updates']<=2*edges*row['iterations']
        if not c.get('search'):assert row['directed_edge_updates']==2*edges*row['iterations']
        assert row['decode_ns']>0
        qs = row['latency_quantiles_seconds'];assert 0<qs['0.5']<=qs['0.95']<=qs['0.99']
        groups[row['job']['id']][row['stage']].append(row)
        if row['stage']=='confirmation':
            assert manifest['target_failures']==20 and manifest['max_shots']==100_000_000
            point = ROOT/'results'/row['job']['id'];audit = json.loads((point/'audit.json').read_text())
            assert audit==json.loads((point/'complete.json').read_text())
            assert audit['confirmation']==row and audit['selection_sha256']==digest(point/'selection.json')
            points.append({'arm':row['job']['arm'],'p':row['job']['physical_p'],'shots':n,'failures':k,
                'ler':k/n,'ci_low':lo,'ci_high':hi,'mean_iterations':row['iterations']/n,
                'mean_directed_edge_updates':row['directed_edge_updates']/n,
                'instrumented_mean_seconds':row['decode_ns']/n/1e9,'controls':c,
                'source_summary':row['directory']+'/summary.json','summary_sha256':digest(directory/'summary.json')})
    for job_id,stages in groups.items():
        chosen = json.loads((ROOT/'results'/job_id/'selection.json').read_text())
        assert len(stages['confirmation'])==1 and stages['confirmation'][0]['controls']==chosen['chosen']
        if stages['coarse']:
            rows = sorted(stages['coarse'],key=order)
            assert {identity(r['controls']) for r in rows[:4]}=={identity(r['controls']) for r in stages['finalist']}
            assert min(stages['finalist'],key=order)['controls']==chosen['chosen']
            assert len(stages['coarse'])==len(run.proposals(stages['confirmation'][0]['job']['arm']))
        else:assert not stages['finalist']
    assert set(groups)==set(receipt['finished_strata']) and len(points)==len(groups)
    index = {(p['arm'],p['p']):p for p in points};comparisons = []
    for rate in plan['source']['rates']:
        for a,b in [('qbp','bp'),('tuned_qbp','qbp'),('tuned_bp','bp'),
                    ('qbp_cs10','tuned_qbp'),('qbp_cs10','cs10'),('qbp_cs10','qbp_osd0'),
                    ('beam128','qbp_cs10'),('relay128','qbp_cs10'),
                    ('tuned_bp','qbp_osd0'),('relay128','tuned_bp')]:
            if (a,rate) not in index or (b,rate) not in index:continue
            x,y = index[a,rate],index[b,rate]
            comparisons.append({'p':rate,'numerator':a,'denominator':b,'ler_ratio':x['ler']/y['ler'] if y['ler'] else None,
                'ci95_overlap':max(x['ci_low'],y['ci_low'])<=min(x['ci_high'],y['ci_high'])})
    complete = {j['id'] for j in plan['jobs'] if (ROOT/'results'/j['id']/'complete.json').exists()}
    checked = {'schema':'lp1054-independent-result-check-v1','verified_sha256':digest(ROOT/'verified.json.gz'),
        'plan_sha256':receipt['plan_sha256'],'audited':len(points),'planned':len(plan['jobs']),
        'completed_simulations':len(complete),'fresh_shots':sum(p['shots'] for p in points),
        'fresh_failures':sum(p['failures'] for p in points),'training_measurements':len(receipt['training']),
        'stage_counts':dict(Counter(r['stage'] for r in receipt['training'])),
        'all_summary_manifest_checks':len(seen),'points':points,'comparisons':comparisons,
        'running':[j for j in plan['jobs'] if j['id'] not in complete],
        'awaiting_audit':[j for j in plan['jobs'] if j['id'] in complete and j['id'] not in groups],
        'scope':'Both logical components; shared iid depolarizing stream; disjoint training/fresh seeds;20-failure precision. Search128 is4x the32 baseline work ceiling. Latency includes provenance instrumentation. Original LP paper has no LER curve/grid/cap;32/.625 borrowed from cited BP-OSD paper and flooding differs from its layered schedule. No native/paper agreement or simultaneous superiority claim.'}
    (ROOT/'CHECKED-RESULTS.json').write_text(json.dumps(checked,sort_keys=True,indent=2)+'\n')
    return checked


def plot(checked):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import LogLocator,LogFormatterMathtext,NullFormatter
    panels = [
        ('BP and pointwise tuning (32 sweeps)',('bp','tuned_bp','qbp','tuned_qbp')),
        ('OSD postprocessing (32 BP sweeps)',('cs10','osd0','qbp','qbp_osd0','qbp_cs10')),
        ('Pointwise-tuned binary search',('tuned_bp','qbp_cs10','beam32','beam128','relay32','relay128'))]
    labels = {'bp':'BP','tuned_bp':'Tuned BP','qbp':'Q-BP','tuned_qbp':'Tuned Q-BP',
        'osd0':'BP+OSD-0','cs10':'BP+CS-10','qbp_osd0':'Q-BP+OSD-0','qbp_cs10':'Q-BP+CS-10',
        'beam32':'Beam32','beam128':'Beam128','relay32':'Relay32','relay128':'Relay128'}
    colors = dict(zip(labels,plt.get_cmap('tab20').colors[::1]))
    fig,axes = plt.subplots(1,3,figsize=(14,4.9),sharex=True,sharey=True)
    for ax,(title,arms) in zip(axes,panels):
        for arm in arms:
            rows = sorted((p for p in checked['points'] if p['arm']==arm),key=lambda p:p['p'])
            if not rows:continue
            rate = np.array([p['ler'] for p in rows]);lo = np.array([p['ci_low'] for p in rows]);hi = np.array([p['ci_high'] for p in rows])
            pointwise = arm.startswith(('tuned_','beam','relay'))
            marker = ('v' if arm.endswith('128') else 's') if pointwise else 'o-'
            ax.errorbar([p['p'] for p in rows],rate,yerr=np.array([rate-lo,hi-rate]),
                fmt=marker,color=colors[arm],label=labels[arm],
                linewidth=1.3,markersize=4,capsize=2,elinewidth=.65,alpha=.95)
        ax.set_title(title,fontsize=10.5);ax.set_yscale('log');ax.set_xlim(.015,.125)
        ax.set_ylim(3e-6,1.15);ax.set_xticks([.02,.04,.06,.08,.10,.12])
        ax.yaxis.set_major_locator(LogLocator(base=10));ax.yaxis.set_major_formatter(LogFormatterMathtext())
        ax.yaxis.set_minor_locator(LogLocator(base=10,subs=np.arange(2,10)));ax.yaxis.set_minor_formatter(NullFormatter())
        ax.grid(True,which='major',linewidth=.55,alpha=.35);ax.grid(True,which='minor',linewidth=.35,alpha=.14)
        ax.set_xlabel('Physical depolarizing probability p');ax.legend(loc='lower right',fontsize=7.5,framealpha=.95)
    axes[0].set_ylabel('Block failure probability (either logical component)')
    fig.suptitle('Original lifted product [[1054,140]] — canonical decoder comparison',fontsize=13)
    fig.text(.5,.025,f'{checked["audited"]}/72 audited points; 95% intervals. Tuned controls vary by rate; only fixed profiles are connected. Search128 permits 4x work. No source LER curve.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.06,1,.94))
    for suffix in ('png','pdf'):fig.savefig(ROOT/('decoder-comparison.'+suffix),dpi=190)
    plt.close(fig)


if __name__=='__main__':
    checked = verify();plot(checked)
    print(json.dumps({k:checked[k] for k in ('audited','planned','completed_simulations','fresh_shots','fresh_failures','training_measurements','all_summary_manifest_checks','running','awaiting_audit')},indent=2))
