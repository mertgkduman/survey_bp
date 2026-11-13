"""Build a descriptive results table from audited receipts, without decoding."""
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CONF=HERE.with_name('mackay-0304161-damping-t100')/'confirmation'
BASE=HERE.with_name('mackay-0304161-inferred-budget')


def read_receipt(root):
    value=json.loads((root/'verified.json').read_text())
    if value['plan_sha256']!=sha256((root/'plan.json').read_bytes()).hexdigest():raise ValueError('receipt plan conflict')
    for row in value['points']:
        if row['rate']!=row['failures']/row['shots']:raise ValueError('rate/count conflict')
        source=root/'results'/row['id']/'summary.json'
        if sha256(source.read_bytes()).hexdigest()!=row['summary_sha256']:raise ValueError('summary hash conflict')
    return value


def main():
    isolated,confirm,base=read_receipt(HERE),read_receipt(CONF),read_receipt(BASE)
    paper=json.loads((HERE.with_name('mackay-0304161-paper-rates')/'source_points.json').read_text())
    evidence=json.loads((HERE/'paper-evidence.json').read_text());now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    records=[]
    for root,receipt in ((HERE,isolated),(CONF,confirm),(BASE,base)):
        for r in receipt['points']:
            if root==BASE and r['arm']!='unicycle_sp':continue
            separate=r['arm']=='binary_separate';u=r['arm']=='unicycle_sp'
            records.append({'code':r['code'],'arm':r['arm'],'physical_p':r['physical_p'],'matched_x_rate':r['matched_x_rate'],
              'channel':r['decoder']['noise_model'],'metric':'quantum_block_failure','status':'complete',
              'damping':r['decoder']['v2c_damping'],'iteration_ceiling':r['decoder']['max_iterations'],
              'error_rate':r['rate'],'classical_error_rate':r['classical_block_error_rate'],
              'ci95_low':r['ci95_low'],'ci95_high':r['ci95_high'],'shots':r['shots'],'failures':r['failures'],
              'mean_iterations':r['iterations']/r['shots'],'iteration_unit':'paired X/Z rounds' if separate else 'branch sweeps' if u else 'joint sweeps' if r['base_arm']=='qbp' else 'sweeps',
              'mean_directed_edge_updates':r['directed_edge_updates']/r['shots'],
              'seed':r['seed'],'evidence_path':str((root/'verified.json').relative_to(REPO)),'summary_sha256':r['summary_sha256']})
    for j in json.loads((CONF/'plan.json').read_text())['jobs']:
        if not any(r['code']==j['code'] and r['arm']==j['arm'] and r['physical_p']==j['physical_p'] for r in records):
            records.append({'code':j['code'],'arm':j['arm'],'physical_p':j['physical_p'],'matched_x_rate':j['matched_x_rate'],
                 'channel':j['decoder']['noise_model'],'metric':'quantum_block_failure','status':'running','damping':j['decoder']['v2c_damping'],'iteration_ceiling':100})
    for p,point in paper['points'].items():
        records.append({'code':'unicycle274','arm':'published_unicycle','physical_p':point['p'],'matched_x_rate':point['p'],
             'channel':'binary_symmetric','metric':'classical_block_error','status':'digitized_approximate',
             'error_rate':point['total_error_approx'],'evidence_path':'data/reproductions/mackay-0304161-paper-rates/source_points.json'})
    for p in evidence['requested_ordinates']:
        records.append({'code':'unicycle74','arm':'published_unicycle','physical_p':p['p_x'],'matched_x_rate':p['p_x'],
             'channel':'binary_symmetric','metric':'classical_block_error','status':p['status'],
             'evidence_path':'data/reproductions/mackay-0304161-isolated-qbp/paper-evidence.json'})
    fields=list(dict.fromkeys(k for r in records for k in r))
    with (HERE/'results-table.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    def value(code,arm,p):
        r=next(r for r in records if r['code']==code and r['arm']==arm and r['physical_p']==p)
        return 'Running' if r['status']=='running' else f'{r["error_rate"]:.4g}'
    lines=['# MacKay Construction-U: isolated decoder and damping results','',f'Snapshot: {now}. Descriptive point estimates from audited receipts; no new sampling or decoding.',
      '', 'These matched-channel tables use identical depolarizing Pauli samples and the independent confirmation seed2026111323. All four methods have a100-full-graph-round ceiling; separate BP uses matched marginal priors2p/3 and Q-BP uses the joint prior p. Both X/Z logical residuals and nonconvergence count toward quantum block failure. Each complete point stopped at20 failures. The20 new d=0 points are fully audited; the existing damping confirmation has39/40 audited points.',
      '', 'Each column below is a quantum block failure probability. Method contrasts compare separate BP and Q-BP at d=0; damping contrasts compare d=0/.1/.95 within Q-BP. These point estimates do not assert simultaneous superiority or statistical equivalence. Work units, mean iterations, actual directed-edge updates, stopping intervals and per-point denominators are retained in results-table.csv.']
    for code in ('unicycle274','unicycle74'):
        lines+=['',f'## Length {code.removeprefix("unicycle")}', '', '| Depolarizing p | Separate BP d=0 | Q-BP d=0 | Q-BP d=.1 | Q-BP d=.95 |', '| ---: | ---: | ---: | ---: | ---: |']
        for p in (.015,.0195,.030,.045,.060):
            lines.append('| '+ ' | '.join([f'{p:g}']+[value(code,a,p) for a in ('binary_separate','qbp_undamped','qbp_baseline','qbp_selected')])+' |')
    lines+=['', '## Original paper comparison', '', 'Source: MacKay, Mitchison and McFadden (2004), https://arxiv.org/abs/quant-ph/0304161v3. The published curve is classical block error on a binary symmetric channel. It uses the two-hypothesis unicycle decoder. Our unicycle adaptation below uses100 iterations per hypothesis (200 maximum total), an inferred rather than source-stated budget. Our ordinary and damped binary BP use X-only noise and T100. Classical and quantum error counts coincide in these listed length274 measurements. All paper ordinates are approximate digitizations.', '', '| X rate | Published unicycle ≈ | Our unicycle | Ordinary BP d=0 | BP d=.85 |', '| ---: | ---: | ---: | ---: | ---: |']
    for p in (.010,.013,.020,.030,.040):
        lines.append('| '+' | '.join([f'{p:g}']+[value('unicycle274',a,p) for a in ('published_unicycle','unicycle_sp','binary_sp_baseline','binary_sp_selected')])+' |')
    lines+=['', 'For length74, the five requested paper ordinates are not reported in inspected arXiv versions1–3 and are blank/not_reported in the CSV. The paper does provide one fixed-target summary: marginal p≈.00681824 for the source convention of quantum error1e-4 / constituent classical error5e-5. That threshold is not a five-rate curve. See PAPER-EVIDENCE.md and paper-evidence.json for all source/member hashes and vector calibration.', '', 'Separate-BP mean rounds are max(X sweeps,Z sweeps); actual component sweeps and directed-edge work account for each component independently. Joint sweeps and unicycle branch sweeps remain explicitly typed. Shared samples across methods or damping settings are not pooled as independent observations.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    meta={'observed_at':now,'rows':len(records),'source_receipts':{str((r/'verified.json').relative_to(REPO)):sha256((r/'verified.json').read_bytes()).hexdigest() for r in (HERE,CONF,BASE)},'csv_sha256':sha256((HERE/'results-table.csv').read_bytes()).hexdigest(),'claim_scope':'Descriptive matched-channel method/damping comparisons, original-paper classical curve separately; missing source ordinates remain unavailable.'}
    (HERE/'report-provenance.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n');print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
