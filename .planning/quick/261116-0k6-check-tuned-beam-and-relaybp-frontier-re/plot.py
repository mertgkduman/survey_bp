"""Separate initial/broader confirmations and same-channel OSD-0 references."""
import gzip
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator,LogFormatterMathtext,NullFormatter

REPO=Path(__file__).resolve().parents[3]
INITIAL=REPO/'data/reproductions/roffe-2005-07016-search'
FRONTIER=INITIAL.with_name('roffe-2005-07016-search-frontier')
receipts=[]
for root in (INITIAL,FRONTIER):
    with gzip.open(root/'verified.json.gz','rt') as stream:receipts.append(json.load(stream))
refs=json.loads((INITIAL.with_name('roffe-2005-07016-osd-fast')/'verified.json').read_text())['points']
plan=json.loads((INITIAL/'plan.json').read_text())
styles={'beam':('#1667a6','o'),'relay':('#d2691e','s')}
fig,axes=plt.subplots(2,4,figsize=(14,7.8),layout='constrained')
for a,p in enumerate((.02,.06)):
    for b,code in enumerate(('toric9','toric11','toric13','toric15')):
        ax=axes[a,b];all_values=[];xs=[.5,1.,2.,4.]
        for cohort,v in enumerate(receipts):
            rows=[r for r in v['points'] if r['job']['code']==code and r['job']['physical_p']==p]
            for row in rows:
                color,marker=styles[row['job']['method']];y=row['rate'] or row['ci95_high'];x=row['runtime_ratio']
                if row['failures']:
                    yerr=[[max(0,y-row['ci95_low'])],[max(0,row['ci95_high']-y)]]
                    ax.errorbar(x,y,yerr=yerr,fmt=marker,color=color,mfc=color if cohort else 'white',
                                ms=6,capsize=3,lw=1,alpha=.95 if cohort else .55,zorder=4 if cohort else 2)
                else:
                    ax.errorbar(x,y,yerr=.3*y,uplims=True,fmt=marker,color=color,
                                mfc=color if cohort else 'white',ms=6,lw=1)
                all_values.append(row);xs.append(x)
            if cohort==1 and not any(r['job']['method']=='beam' for r in rows):
                ax.text(.97,.94,'Broader beam pending',transform=ax.transAxes,ha='right',va='top',fontsize=8,color='#555')
        ref=next((r for r in refs if r['code']==code and r['physical_p']==p and r['arm']=='bp_osd0'),None)
        if ref:
            y=ref['rate'] or ref['ci95_high'];all_values.append(ref)
            ax.errorbar(1,y,yerr=[[max(0,y-ref['ci95_low'])],[max(0,ref['ci95_high']-y)]],
                        fmt='D',color='black',ms=5,capsize=3,lw=1,zorder=5)
        else:ax.text(.5,.04,'OSD-0 reference pending',transform=ax.transAxes,ha='center',fontsize=8,color='#555')
        ax.set(xscale='log',yscale='log',title=f'n = {plan["codes"][code]["n"]}, p = {p:g}')
        ax.set_xlim(min(xs)/1.5,max(xs)*1.5)
        lows=[r['ci95_low'] for r in all_values if r['ci95_low']>0]
        highs=[r['ci95_high'] for r in all_values]
        if lows:ax.set_ylim(10**math.floor(math.log10(min(lows))),10**math.ceil(math.log10(max(highs))))
        for axis in (ax.xaxis,ax.yaxis):
            axis.set_major_locator(LogLocator(base=10));axis.set_major_formatter(LogFormatterMathtext())
            axis.set_minor_locator(LogLocator(base=10,subs=range(2,10)));axis.set_minor_formatter(NullFormatter())
        for budget in (.5,1.,2.,4.):ax.axvline(budget,color='#999',ls=':',lw=.6,zorder=0)
        ax.grid(which='major',alpha=.3);ax.grid(which='minor',alpha=.1)
        if a==1:ax.set_xlabel('Mean decoder time /\nsame-CPU OSD-0')
        if b==0:ax.set_ylabel('Block logical failure rate')
fig.suptitle(f'Broader search: {len(receipts[1]["finished_strata"])}/218 workers audited\nX-only, independent confirmations; pointwise 95% intervals; exact configurations remain separate',fontsize=13)
handles=[]
for method in ('beam','relay'):
    color,marker=styles[method]
    for cohort,label in ((0,'Initial'),(1,'Broader')):
        handles.append(Line2D([],[],marker=marker,color=color,mfc=color if cohort else 'white',ls='',label=label+' '+method))
handles.append(Line2D([],[],marker='D',color='black',ls='',label='BP+OSD-0'))
fig.legend(handles=handles,loc='outside lower center',ncol=5,frameon=False,fontsize=10)
for suffix in ('png','pdf'):fig.savefig(Path(__file__).with_name('ler-latency.'+suffix),dpi=180)
