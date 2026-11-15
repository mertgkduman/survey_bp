"""Scientific per-cap curves at pX=.02, keeping the two channels explicit."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, LogFormatterMathtext, LogLocator, NullFormatter
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'


def main():
    comparisons = json.loads((HERE / 'point-comparisons.json').read_text())
    with (ROOT / 'iteration-results.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    osd = json.loads((REPO / 'data/reproductions/roffe-2005-07016-osd-fast/verified.json').read_text())['points']
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    for column, code in enumerate(('toric9', 'toric11', 'toric13', 'toric15')):
        for row_index, family in enumerate(('binary_css', 'bp4')):
            ax = axes[row_index, column]
            comparison = next(c for c in comparisons if c['code'] == code and c['family'] == family and c['matched_x_rate'] == .02)
            selected = [r for r in rows if r['code'] == code and r['family'] == family and float(r['matched_x_rate']) == .02]
            lower = [float(r['ci95_low']) for r in selected]
            upper = [float(r['ci95_high']) for r in selected]
            for role, color, marker, linestyle in [('previous_damping', '#2464a4', 'o', '--'), ('joint_selected', '#b85b08', '^', '-')]:
                values = sorted([r for r in selected if role in r['roles'].split(',')], key=lambda r: int(r['iteration_cap']))
                x = np.array([int(r['iteration_cap']) for r in values]); y = np.array([float(r['ler']) for r in values])
                low = np.array([float(r['ci95_low']) for r in values]); high = np.array([float(r['ci95_high']) for r in values])
                ax.errorbar(x, y, yerr=np.stack((y-low, high-y)), color=color, linestyle=linestyle, linewidth=1.2, capsize=2, alpha=.9)
                for r in values:
                    ax.plot(int(r['iteration_cap']), float(r['ler']), marker=marker, markersize=5,
                            markerfacecolor=color if float(r['runtime_ratio']) <= 1.1 else 'white', markeredgecolor=color)
            if family == 'binary_css':
                reference = next((r for r in osd if r['code'] == code and r['arm'] == 'bp_osd0' and r['physical_p'] == .02), None)
                if reference:
                    ax.axhline(reference['rate'], color='#348443', linewidth=1.3, linestyle=':')
                    lower.append(reference['rate'])
                else: ax.text(.04, .05, 'OSD0 reference still running', transform=ax.transAxes, fontsize=8)
            ax.axvline(comparison['n'], color='#666666', linewidth=.8, linestyle=':')
            ax.set_xscale('log'); ax.set_yscale('log')
            caps = sorted({int(r['iteration_cap']) for r in selected})
            ticks = sorted({min(caps, key=lambda c: abs(np.log(c/target))) for target in np.geomspace(min(caps), max(caps), 3)})
            ax.xaxis.set_major_locator(FixedLocator(ticks)); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{int(v)}'))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_ylim(10**np.floor(np.log10(min(lower)*.95)), 10**np.ceil(np.log10(max(upper)*1.05)))
            ax.yaxis.set_major_locator(LogLocator(base=10)); ax.yaxis.set_major_formatter(LogFormatterMathtext())
            ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
            ax.yaxis.set_minor_formatter(NullFormatter())
            ax.grid(which='major', alpha=.25); ax.grid(which='minor', axis='y', alpha=.09)
            ax.set_title(f'[[{comparison["n"]},2,{(9,11,13,15)[column]}]]', fontsize=11)
            ax.set_xlabel('Iteration cap T')
            if column == 0: ax.set_ylabel(('BP, X-only p=.02' if family == 'binary_css' else 'Q-BP, depolarizing p=.03')+'\nBlock logical failure rate')
    handles = [Line2D([], [], color='#2464a4', marker='o', linestyle='--', label='Previous damping controls'),
               Line2D([], [], color='#b85b08', marker='^', label='Joint selected controls'),
               Line2D([], [], color='#348443', linestyle=':', label='BP+OSD0, X-only reference'),
               Line2D([], [], color='#666666', marker='o', markerfacecolor='white', linestyle='None', label='Hollow marker: >1.1× reference time')]
    fig.legend(handles=handles, loc='upper center', ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(.5, .96))
    fig.suptitle('Completed iteration sweeps: more work versus joint numerical tuning', fontsize=13, y=.995)
    fig.text(.5, .012, 'Fresh 20-failure measurements; error bars: pointwise 95% intervals. Shared shot prefixes within each channel. Vertical dotted line: T=n. BP and Q-BP use different noise channels.', ha='center', fontsize=8)
    fig.subplots_adjust(left=.075, right=.99, bottom=.10, top=.86, hspace=.38, wspace=.35)
    fig.savefig(HERE / 'iteration-comparison.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__': main()
