"""Inventory primary source figures; extract only the actual N74 summary point."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent

def extract(archives):
    versions=[];summary=None
    for version,path in sorted(archives.items()):
        with tarfile.open(path) as archive:
            figures=[]
            for m in archive.getmembers():
                if m.name.endswith(('.ps','.eps','.pdf')):
                    data=archive.extractfile(m).read()
                    figures.append({'member':m.name,'sha256':sha256(data).hexdigest()})
                    if version==3 and m.name=='figs/QSUMMARYUBNM.ps':summary=data
            versions.append({'version':version,'url':f'https://arxiv.org/src/quant-ph/0304161v{version}',
                             'archive_sha256':sha256(path.read_bytes()).hexdigest(),'figures':figures})
    if summary is None:raise ValueError('missing v3 performance summary')
    text=summary.decode()
    for token in ('3651 1574 Box','(74\\(U\\)) Rshow','(0.001) Cshow','(0.01) Cshow'):
        if token not in text:raise ValueError('summary coordinates or code identity changed')
    p=.001*10**((3651-1601)/(4060-1601))
    quantum_rate=(1574-784)/(4031-784)
    if abs(quantum_rate-18/74)>.001:raise ValueError('summary marker does not match N74 quantum rate')
    return {'schema':'mackay-length74-paper-evidence-v1',
      'paper':'https://arxiv.org/abs/quant-ph/0304161v3',
      'scope':'arXiv source versions1–3 and current42-page PDF; journal DOI retrieval was unavailable',
      'source_inventory':versions,
      'finding':'No length74 block-error-versus-noise curve is present. UCY.73 is a parity matrix; QSUMMARYUBNM is performance at a fixed error target. BSClDSC.273.82C is length274.',
      'pdf_references':{'construction':'Figure11, printed page27','length274_curve':'Figure16, printed page34','fixed_error_summary':'Figure17, printed page35'},
      'requested_ordinates':[{'p_x':rate,'paper_block_error':None,'status':'not_reported_in_inspected_sources'} for rate in (.010,.013,.020,.030,.040)],
      'available_summary_point':{'code_n':74,'quantum_k':18,'member':'figs/QSUMMARYUBNM.ps',
         'sha256':sha256(summary).hexdigest(),'marker_plot_xy':[3651,1574],
         'x_axis':'logarithmic marginal flip probability',
         'x_calibration':[{'plot_x':1601,'p_x':.001},{'plot_x':4060,'p_x':.01}],
         'p_x_approx':p,'source_target_classical_constituent_block_error':.00005,
         'source_target_quantum_block_error_convention':.0001,
         'meaning':'One marginal noise threshold at a fixed failure target. Not an ordinate at any of the five requested rates; cannot infer a curve or error bars.'},
      'prohibited_substitutions':['Do not interpolate a single threshold into five error-rate values.',
           'Do not substitute our simulations, the N274 curve, or the N73 classical cyclic code for N74 source measurements.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v1',type=Path,required=True);p.add_argument('--v2',type=Path,required=True);p.add_argument('--v3',type=Path,required=True);a=p.parse_args()
    result=extract({1:a.v1,2:a.v2,3:a.v3});(HERE/'paper-evidence.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['available_summary_point'],indent=2))
