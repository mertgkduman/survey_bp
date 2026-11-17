"""Verify released Fig1 evidence and reproduce its source-data figure."""
from pathlib import Path
import csv
from hashlib import sha256
import json
import math
import numpy as np
import stim
from bp_registry.circuit.dem import DemBinaryModel

ROOT=Path(__file__).resolve().parent


def check():
    source=json.loads((ROOT/'source.json').read_text());schedules=json.loads((ROOT/'phase-schedules.json').read_text())
    cases=[]
    for item in source['circuits']:
        path=ROOT/'circuits'/item['file'];assert sha256(path.read_bytes()).hexdigest()==item['sha256']
        circuit=stim.Circuit.from_file(str(path));dem=circuit.detector_error_model();model=DemBinaryModel.from_dem(dem)
        seen={};conflicts=0
        for inst in dem.flattened():
            if inst.type!='error':continue
            ds=set();obs=set()
            for t in inst.targets_copy():
                if t.is_relative_detector_id():
                    if t.val in ds:ds.remove(t.val)
                    else:ds.add(t.val)
                elif t.is_logical_observable_id():
                    if t.val in obs:obs.remove(t.val)
                    else:obs.add(t.val)
            key=frozenset(ds)
            if key in seen:raise AssertionError('source detector-only merging is not an identity')
            seen[key]=frozenset(obs)
        assert len(seen)==item['num_error_mechanisms']==model.table.variable_count
        assert circuit.num_detectors==item['num_detectors'] and circuit.num_observables==item['num_observables']
        assert min(np.diff(model.row_ptr))>10 # even ten Beam fixations cannot create a unary check
        cases.append({'file':item['file'],'circuit_sha256':item['sha256'],'dem_execution_sha256':model.execution_sha256,
                      'checks':model.table.check_count,'variables':model.table.variable_count,'edges':len(model.variables),
                      'minimum_check_degree':int(min(np.diff(model.row_ptr))),'detector_merge_collisions':0})
    by_basis={}
    for path in sorted((ROOT/'source-data').glob('*.csv')):
        if path.name=='paper_figure_data.csv':continue
        with path.open() as f:
            for row in csv.DictReader(f):
                meta=json.loads(row['json_metadata']);params=json.loads(row['decoder_params'])
                key=(meta['code'],float(meta['p_CNOT']),row['decoder'],meta['x_or_z'])
                assert key not in by_basis and int(row['discards'])==0
                if row['decoder']=='PriorTilt_3phase':
                    sch=schedules[meta['code']][str(meta['p_CNOT'])]
                    assert params['schedule']=={k:sch[k] for k in ('ends','phases')}
                    assert (params['initial_iters'],params['round_len'],params['max_rounds'])==(60,6,3000)
                if row['decoder']=='BeamSearch32':assert params=={'beam_width':32,'initial_iters':40,'iters_per_round':30,'max_rounds':10}
                if row['decoder']=='RelayBP':
                    assert [params['initial_gamma'],params['gamma_lb'],params['gamma_ub']]==source['relay_gammas'][meta['code']]
                    assert (params['initial_iters'],params['iters_per_round'],params['max_rounds'])==(80,60,301)
                by_basis[key]={**meta,'shots':int(row['shots']),'errors':int(row['errors']),'params':params,'file':path.name}
    assert len(by_basis)==78
    with (ROOT/'source-data/paper_figure_data.csv').open() as f:tidy=list(csv.DictReader(f))
    for row in tidy:
        key=(row['code'],float(row['p']),row['decoder'],row['basis']);r=by_basis[key]
        assert int(row['shots'])==r['shots'] and int(row['errors'])==r['errors']
        assert math.isclose(float(row['ler_per_cycle']),r['errors']/r['shots']/r['syndrome_rounds'],rel_tol=1e-13)
    rows=[]
    for code,p,method,basis in sorted(by_basis):
        if basis!='x':continue
        x=by_basis[(code,p,method,'x')];z=by_basis[(code,p,method,'z')];d=x['syndrome_rounds'];assert d==z['syndrome_rounds']
        rows.append({'code':code,'p':p,'method':method,'cycles':d,'x_shots':x['shots'],'x_errors':x['errors'],
                     'z_shots':z['shots'],'z_errors':z['errors'],
                     'ler_per_cycle':(x['errors']/x['shots']+z['errors']/z['shots'])/d,
                     'published_1sigma':math.sqrt(x['errors']/x['shots']**2+z['errors']/z['shots']**2)/d})
    with (ROOT/'source-figure1.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    evidence={'source_commit':source['commit'],'circuits':cases,'source_basis_rows':78,'source_figure_points':39,
              'schedule_precision':'full released values; paper table is rounded','metric':'(errors_X/shots_X + errors_Z/shots_Z)/cycles',
              'canonical_numeric_difference':'existing total-minus-excluded-message float64 order; paper ties at zero; no historical kernel edited'}
    (ROOT/'source-contract.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return rows


def plot_source(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(13,3.7),constrained_layout=True)
    colors={'PriorTilt_3phase':'#087d78','RelayBP':'#b47412','BeamSearch32':'#5066aa'}
    for ax,code in zip(axes,['BB144','BB70','GB102']):
        for method,color in colors.items():
            values=sorted([r for r in rows if r['code']==code and r['method']==method],key=lambda r:r['p'])
            ax.errorbar([r['p'] for r in values],[r['ler_per_cycle'] for r in values],yerr=[r['published_1sigma'] for r in values],label=method,color=color,marker='o',capsize=2,linewidth=1.3)
        ax.set(xscale='log',yscale='log',title=code,xlabel='Physical circuit error probability p')
        ax.grid(True,which='major',alpha=.3);ax.grid(True,which='minor',alpha=.1)
    axes[0].set_ylabel('LER per syndrome cycle · X + Z');axes[-1].legend(fontsize=8)
    fig.suptitle('Fig. 1 — reconstructed from author-released counts (1σ bars)')
    fig.savefig(ROOT/'source-figure1.png',dpi=180);fig.savefig(ROOT/'source-figure1.pdf');plt.close(fig)


if __name__=='__main__':
    rows=check();plot_source(rows);print('26 exact circuits; 78 basis rows; 39 source figure points verified.')
