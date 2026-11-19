"""Publish complete, freshly audited paired-memory points; never pilot estimates."""
import csv
import io
import json
from pathlib import Path
import os
import numpy as np
import run

METHOD_NAMES={'priortilt':'PriorTilt_3phase','relay5':'RelayBP-5'}


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
    source={(r['code'],float(r['p']),r['method']):r for r in csv.DictReader((run.ROOT/'source-table4.csv').open())};out=[]
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


def collect():
    import parallel
    parallel.load_amendment()
    with run.lock(run.ROOT/'publish.lock',True):
        plan=run.load();values=rows(plan)
        fields=list(values[0]) if values else ['point','code','p','method','cycles','ler_per_cycle','ci95_low','ci95_high']
        stream=io.StringIO();w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(values)
        tmp=run.ROOT/'comparison.csv.tmp';tmp.write_text(stream.getvalue());os.replace(tmp,run.ROOT/'comparison.csv')
        text=['# PriorTilt Table 4: XYZ joint-DEM reproduction','',f'{len(values)}/2 paired-memory decoder points passed fresh full worker audits; 50 process workers per point.',
            '', 'Source: [Ye and Delfosse, arXiv:2611.13373v1, Table 4](https://arxiv.org/html/2611.13373v1). BB144 [[144,12,12]], p=.003, 12 cycles. The full joint detector models have 1728 checks and about67800 fault mechanisms per basis.',
            '', 'PriorTilt:60+6000x6=36060 sweeps, source three-phase parameters. RelayBP-5:80+600x60=36080 sweeps, five converged legs including duplicate solutions, first minimum original-prior LLR score. Canonical float64 reduction and indexed randomness differ from the native reference; adaptation rather than bitwise native identity.',
            '', 'Metric=(X-memory observable error rate+Z-memory observable error rate)/12. Nonconvergence is recorded separately. Each basis stops at20 observable errors or100M shots. Local bars are pointwise at-least95% simultaneous X/Z intervals; author precision and1-sigma bars are separate. Qualification and incomplete points are excluded.',
            '', '| Decoder | X errors/shots | Z errors/shots | Local LER/cycle [95%] | Paper LER/cycle | Paper inside local interval |',
            '|---|---:|---:|---:|---:|---|']
        for r in values:
            text.append(f"| {r['method']} | {r['x_errors']}/{r['x_shots']} | {r['z_errors']}/{r['z_shots']} | {r['ler_per_cycle']:.6g} [{r['ci95_low']:.6g}, {r['ci95_high']:.6g}] | {r['paper_ler_per_cycle']:.6g} | {r['paper_inside_local95']} |")
        if not values:text+=['','No completed local measurements yet. Author measurements are in source-table4.csv.']
        text+=['','CSV includes both denominators, failures, nonconvergence, mean all-path sweeps, directed edge updates, random draws, bias updates and instrumented decoder latency per basis. Concurrent50-CPU timing is not a matched single-core or paper-hardware speed comparison. Sampling/evaluation/audit/I/O are outside decoder latency. All sealed speculative work remains separately recorded and fully audited; only ordered exact stopping prefixes enter estimates. Unsealed interrupted work is unmeasured. Publication rehashes bound event chunks and shared samples.']
        (run.ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n')
        print('Published',len(values),'/2 fully audited XYZ points',flush=True)


if __name__=='__main__':collect()
