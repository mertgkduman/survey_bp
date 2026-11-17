"""Publish complete, freshly audited paired-memory points; never pilot estimates."""
import csv
import io
import json
from pathlib import Path
import os
import numpy as np
import run

METHOD_NAMES={'priortilt':'PriorTilt_3phase','relay':'RelayBP','beam':'BeamSearch32'}


def audited(plan,job):
    root=run.ROOT/'results'/job['id'];path=root/'audit.json'
    if not path.exists():return None
    a=json.loads(path.read_text())
    if a!=json.loads((root/'complete.json').read_text()) or a['plan_sha256']!=run.sha(run.ROOT/'plan.json') or a['job']!=job:raise ValueError('audit receipt identity changed')
    if a['manifest_sha256']!=run.sha(root/'manifest.json'):raise ValueError('audited manifest changed')
    from dataclasses import asdict
    if a['resolved_policy']!=json.loads(json.dumps(asdict(run.spec_for(job)))):raise ValueError('audited policy changed')
    for basis,s in a['bases'].items():
        if s!=run.terminal({k:v for k,v in s.items() if k not in ('rate','ci975','stop_reason')},plan):raise ValueError('terminal counts or uncertainty changed')
        for name,digest in s['chunks'].items():
            marker=root/basis/name
            if run.sha(marker)!=digest:raise ValueError('audited marker changed')
            meta=json.loads(marker.read_text())
            if run.sha(marker.with_suffix('.npz'))!=meta['sha256']:raise ValueError('audited event ledger changed')
            run.verify_noise_binding(plan,job,basis,meta['start'],meta)
    return a


def rows(plan):
    source={(r['code'],float(r['p']),r['method']):r for r in csv.DictReader((run.ROOT/'source-figure1.csv').open())};out=[]
    for j in plan['jobs']:
        a=audited(plan,j)
        if a is None:continue
        x,z=a['bases']['x'],a['bases']['z'];cycles=j['cycles'];p=source[j['code'],j['p'],METHOD_NAMES[j['method']]]
        rate=(x['rate']+z['rate'])/cycles;low=(x['ci975'][0]+z['ci975'][0])/cycles;high=(x['ci975'][1]+z['ci975'][1])/cycles
        row={'point':j['id'],'code':j['code'],'p':j['p'],'method':j['method'],'cycles':cycles,'ler_per_cycle':rate,'ci95_low':low,'ci95_high':high,
             'paper_ler_per_cycle':float(p['ler_per_cycle']),'paper_1sigma':float(p['published_1sigma']),
             'local_over_paper':rate/float(p['ler_per_cycle']),'paper_inside_local95':low<=float(p['ler_per_cycle'])<=high,
             'audit_sha256':run.sha(run.ROOT/'results'/j['id']/'audit.json')}
        for basis,s in [('x',x),('z',z)]:
            row.update({basis+'_'+k:s[k] for k in ('shots','errors','nonconvergence','stop_reason')})
            row[basis+'_observable_rate']=s['rate'];row[basis+'_ci975_low'],row[basis+'_ci975_high']=s['ci975']
            for k in ('iterations','directed_edge_updates','random_draws','biased_node_updates'):row[basis+'_mean_'+k]=s[k]/s['shots']
            row[basis+'_mean_decode_ms']=s['decode_ns']/s['shots']/1e6
        out.append(row)
    return out


def plot(values):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    source=list(csv.DictReader((run.ROOT/'source-figure1.csv').open()))
    colors={'priortilt':'#087d78','relay':'#b47412','beam':'#5066aa'}
    fig,axes=plt.subplots(1,3,figsize=(13,4.2),constrained_layout=True)
    for ax,code in zip(axes,('BB144','BB70','GB102')):
        for method,color in colors.items():
            s=sorted([r for r in source if r['code']==code and r['method']==METHOD_NAMES[method]],key=lambda r:float(r['p']))
            ax.errorbar([float(r['p']) for r in s],[float(r['ler_per_cycle']) for r in s],yerr=[float(r['published_1sigma']) for r in s],color=color,marker='o',linestyle='--',linewidth=1,markersize=3,alpha=.6,label=method+' · paper (1σ)')
            v=sorted([r for r in values if r['code']==code and r['method']==method],key=lambda r:r['p'])
            if v:
                ax.errorbar([r['p'] for r in v],[r['ler_per_cycle'] or r['ci95_high'] for r in v],
                    yerr=np.array([[r['ler_per_cycle']-r['ci95_low'] if r['ler_per_cycle'] else 0. for r in v],
                                   [r['ci95_high']-r['ler_per_cycle'] if r['ler_per_cycle'] else 0. for r in v]]),
                    color=color,marker='s',linestyle='-',linewidth=1.4,markersize=4,capsize=3,label=method+' · canonical (95%)')
                for r in v:
                    if not r['ler_per_cycle']:ax.annotate('',(r['p'],r['ci95_high']*.65),(r['p'],r['ci95_high']),arrowprops={'arrowstyle':'->','color':color})
        ax.set(xscale='log',yscale='log',xlabel='Physical circuit error probability p',title=code)
        ax.grid(True,which='major',alpha=.3);ax.grid(True,which='minor',alpha=.1)
    axes[0].set_ylabel('(X-memory + Z-memory observable error) / cycles')
    axes[-1].legend(fontsize=6.5,loc='best')
    fig.suptitle(f'PriorTilt Fig. 1 · {len(values)}/39 complete canonical points · source precision shown separately')
    for suffix in ('png','pdf'):fig.savefig(run.ROOT/('comparison.'+suffix),dpi=180)
    plt.close(fig)


def collect():
    with run.lock(run.ROOT/'publish.lock',True):
        plan=run.load();values=rows(plan)
        fields=list(values[0]) if values else ['point','code','p','method','cycles','ler_per_cycle','ci95_low','ci95_high']
        stream=io.StringIO();w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(values)
        tmp=run.ROOT/'comparison.csv.tmp';tmp.write_text(stream.getvalue());os.replace(tmp,run.ROOT/'comparison.csv')
        text=['# PriorTilt Fig. 1 — canonical reproduction campaign','',f'{len(values)}/39 complete plotted points passed the fresh-process full-ledger audit. Each point uses one CPU for X/Z memories sequentially.',
            '', 'Source: [Ye and Delfosse, arXiv:2611.13373v1](https://arxiv.org/html/2611.13373v1), Fig. 1; exact released circuits, rates and full-precision three-phase schedules. This is a canonical float64 adaptation; native prefix/suffix arithmetic and RNG are separate references.',
            '', 'Local stopping is 20 observable errors or 100 million decoded shots **per memory basis**. The authors use larger counts. Qualification shots and unfinished points are excluded. Nonconvergence is recorded separately, not automatically counted as a logical error. Local bars are at-least-95% simultaneous X/Z bounds; source bars are published 1σ. Agreement is pointwise and limited by local precision.',
            '', 'The CSV retains both denominators, errors, nonconvergence, mean all-path BP sweeps, directed edge updates, random draws, biased-node updates and measured instrumented controller latency per basis. Latency includes trace/provenance and Python admission but excludes sampling, evaluation, audit and I/O; no native runtime comparison is claimed.',
            '', '| Code | p | Decoder | X errors / shots | Z errors / shots | Local LER/cycle (95%) | Paper LER/cycle | Local/paper | Paper inside local interval |',
            '|---|---:|---|---:|---:|---:|---:|---:|---|']
        for r in values:
            text.append(f"| {r['code']} | {r['p']:.4g} | {r['method']} | {r['x_errors']}/{r['x_shots']} | {r['z_errors']}/{r['z_shots']} | {r['ler_per_cycle']:.4g} [{r['ci95_low']:.4g}, {r['ci95_high']:.4g}] | {r['paper_ler_per_cycle']:.4g} | {r['local_over_paper']:.3g} | {r['paper_inside_local95']} |")
        if not values:text+=['','No completed local measurements yet. The plot currently contains source measurements only.']
        text+=['','![Source and canonical comparison](comparison.png)','','The event ledgers remain under ignored `results/`; audit receipts and their hashes bind the published rows. `run.py --index N --audit` independently reevaluates all original DEM detector and logical equations, reconciles work/lineage and replays chunk endpoints before issuing a receipt. Publication rehashes bound chunks and shared samples.']
        (run.ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n');plot(values)
        print(f'Published {len(values)}/39 audited points',flush=True)


if __name__=='__main__':collect()
