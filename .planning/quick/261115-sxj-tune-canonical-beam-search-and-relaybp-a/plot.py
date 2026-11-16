"""Pointwise measured latency/LER tradeoffs; no unlike controls are connected."""
import gzip
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, LogFormatterMathtext, NullFormatter

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'data/reproductions/roffe-2005-07016-search'
with gzip.open(ROOT/'verified.json.gz','rt') as stream:receipt=json.load(stream)
reference=json.loads((ROOT.with_name('roffe-2005-07016-osd-fast')/'verified.json').read_text())['points']
plan=json.loads((ROOT/'plan.json').read_text())
fig,axes=plt.subplots(2,4,figsize=(14,7.5),layout='constrained')
styles={'beam':('#1667a6','o'),'relay':('#d2691e','s')}
for row,p in enumerate((.02,.06)):
    for col,code in enumerate(('toric9','toric11','toric13','toric15')):
        ax=axes[row,col];values=[r for r in receipt['points'] if r['job']['code']==code and r['job']['physical_p']==p]
        old=next((r for r in reference if r['code']==code and r['physical_p']==p and r['arm']=='bp_osd0'),None)
        for item in values:
            color,marker=styles[item['job']['method']]
            y=item['rate'] or item['ci95_high'];x=item['runtime_ratio']
            ax.errorbar(x,y,yerr=[[max(0,y-item['ci95_low'])],[max(0,item['ci95_high']-y)]],
                        fmt=marker,color=color,ms=6,capsize=3,lw=1,alpha=.9)
        if old:
            y=old['rate'] or old['ci95_high']
            ax.errorbar(1,y,yerr=[[max(0,y-old['ci95_low'])],[max(0,old['ci95_high']-y)]],
                        fmt='D',color='black',ms=5,capsize=3,lw=1)
        if not values:ax.text(.04,.94,'Search results pending',transform=ax.transAxes,va='top',color='#555',fontsize=9)
        if not old:ax.text(.5,.08,'OSD-0 result pending',transform=ax.transAxes,ha='center',color='#555',fontsize=8)
        ax.set(xscale='log',yscale='log',title=f'n = {plan["codes"][code]["n"]}, p = {p:g}')
        for budget in (.5,1.,2.,4.):ax.axvline(budget,color='#a5a5a5',lw=.6,ls=':',zorder=0)
        for axis in (ax.xaxis,ax.yaxis):
            axis.set_major_locator(LogLocator(base=10));axis.set_major_formatter(LogFormatterMathtext())
            axis.set_minor_locator(LogLocator(base=10,subs=range(2,10)))
            axis.set_minor_formatter(NullFormatter())
        xs=[r['runtime_ratio'] for r in values]+[.5,1.,2.,4.]
        ax.set_xlim(min(xs)/1.5,max(xs)*1.5)
        visible=values+([old] if old else [])
        if visible:
            lows=[r['ci95_low'] for r in visible if r['ci95_low']>0]
            highs=[r['ci95_high'] for r in visible]
            if lows:ax.set_ylim(10**math.floor(math.log10(min(lows))),10**math.ceil(math.log10(max(highs))))
        ax.grid(which='major',alpha=.3);ax.grid(which='minor',alpha=.1)
        if row==1:ax.set_xlabel('Mean decoder time /\nsame-CPU OSD-0')
        if col==0:ax.set_ylabel('Block logical failure rate')
fig.suptitle(f'Initial beam/RelayBP search: {len(receipt["finished_strata"])}/218 audited workers\nX-only; separate exact configurations, pointwise 95% intervals; stronger finalist study running',fontsize=13)
fig.legend(handles=[Line2D([],[],marker='o',color=styles['beam'][0],ls='',label='Beam search'),
                    Line2D([],[],marker='s',color=styles['relay'][0],ls='',label='RelayBP'),
                    Line2D([],[],marker='D',color='black',ls='',label='BP+OSD-0')],
           loc='outside lower center',ncol=3,frameon=False)
for suffix in ('png','pdf'):fig.savefig(Path(__file__).with_name('ler-latency.'+suffix),dpi=180)
