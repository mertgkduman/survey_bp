"""Independently reconcile completed holdout evidence; no new simulations."""
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, LogFormatterMathtext, LogLocator
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')


def assess():
    training = rt.load(ROOT)
    confirmed = ROOT / 'confirmation'
    plan = rt.load(confirmed)
    receipt = json.loads((confirmed / 'verified.json').read_text())
    selection = json.loads((ROOT / 'selection.json').read_text())
    tuning = json.loads((ROOT / 'verified.json').read_text())
    source = json.loads((ORIGINAL / 'source_points.json').read_text())
    assert selection['plan_sha256'] == tuning['plan_sha256'] == rt.sha(ROOT / 'plan.json')
    assert selection['tuning_receipt_sha256'] == rt.sha(ROOT / 'verified.json')
    assert len(tuning['points']) == tuning['planned_points'] == len(training['jobs']) == 1526
    assert sum(r['shots'] for r in tuning['points']) == 1562624
    assert receipt['plan_sha256'] == rt.sha(confirmed / 'plan.json')
    assert len(receipt['points']) == receipt['planned_points'] == len(plan['jobs']) == 436
    selected = {(e['code'], e['base_arm']): e['damping'] for e in selection['selected']}
    assert len(selected) == 8
    jobs = {j['id']: j for j in plan['jobs']}
    rows, groups = [], {}
    for r in receipt['points']:
        job = jobs[r['id']]
        assert all(r[k] == v for k, v in job.items())
        c = plan['codes'][r['code']]
        n, k = r['shots'], r['failures']
        assert k == 20 and r['stop_reason'] == 'target_block_failures'
        assert sum(r['counts'].values()) == n and r['rate'] == k/n
        assert r['seed'] == training['selection']['confirmation_seed']
        assert r['seed'] != training['jobs'][0]['seed']
        assert r['selection_sha256'] == rt.sha(ROOT / 'selection.json')
        assert r['decoder']['max_iterations'] == c['n']
        assert r['decoder']['v2c_damping'] == (0. if r['role'] == 'baseline' else selected[r['code'], r['base_arm']])
        assert r['directed_edge_updates'] == 2*r['graph_edges']*r['iterations']
        assert rt.sha(confirmed / 'results' / r['id'] / 'summary.json') == r['summary_sha256']
        # Independent exact interval for a failure-target stopping rule.
        lo = float(beta.ppf(.025, k, n-k+1))
        hi = 1. if n == k else float(beta.ppf(.975, k, n-k))
        assert math.isclose(lo, r['ci95_low'], rel_tol=1e-12)
        assert math.isclose(hi, r['ci95_high'], rel_tol=1e-12)
        joint = r['base_arm'] == 'qbp_ms'
        assert r['physical_p'] == (1.5*r['matched_x_rate'] if joint else r['matched_x_rate'])
        paper = next(p['block_ler_approx'] for p in source['curves'][str(c['d'])] if p['p'] == r['matched_x_rate'])
        rows.append({'code': r['code'], 'n': c['n'], 'distance': c['d'], 'family': r['base_arm'],
                     'role': r['role'], 'noise': r['decoder']['noise_model'],
                     'damping': r['decoder']['v2c_damping'], 'iteration_cap': c['n'],
                     'matched_x_rate': r['matched_x_rate'], 'physical_p': r['physical_p'],
                     'shots': n, 'logical_failures': k, 'block_ler': k/n,
                     'ci95_low': lo, 'ci95_high': hi,
                     'mean_iterations': r['iterations']/n,
                     'mean_directed_edge_updates': r['directed_edge_updates']/n,
                     'type_i': r['counts']['type_i'], 'type_ii': r['counts']['type_ii'],
                     'paper_ordinary_bp_approx': None if joint else paper,
                     'ledger_sha256': r['ledger_sha256'], 'summary_sha256': r['summary_sha256']})
        groups.setdefault((r['code'], r['base_arm'], r['role']), []).append(r)
    comparisons = []
    for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['d']):
        for family in ('binary_ms', 'qbp_ms'):
            baseline = sorted(groups[code, family, 'baseline'], key=lambda r: r['matched_x_rate'])
            damped = sorted(groups[code, family, 'selected'], key=lambda r: r['matched_x_rate'])
            expected = [p['p'] for p in source['curves'][str(plan['codes'][code]['d'])]]
            assert [r['matched_x_rate'] for r in baseline] == [r['matched_x_rate'] for r in damped] == expected
            means = {role: {'ler': sum(r['rate'] for r in points)/len(points),
                            'iterations': sum(r['iterations']/r['shots'] for r in points)/len(points)}
                     for role, points in [('baseline', baseline), ('selected', damped)]}
            comparisons.append({'code': code, 'family': family, 'damping': selected[code, family],
                                'rates': len(expected), 'equal_rate_means': means,
                                'ler_reduction_fraction': 1-means['selected']['ler']/means['baseline']['ler'],
                                'iteration_reduction_fraction': 1-means['selected']['iterations']/means['baseline']['iterations'],
                                'lower_point_estimates': sum(a['rate'] < b['rate'] for a, b in zip(damped, baseline, strict=True))})
    result = {'schema': 'roffe-heldout-damping-assessment-v1', 'confirmation_points': len(rows),
              'confirmation_shots': sum(r['shots'] for r in receipt['points']),
              'confirmation_failures': sum(r['failures'] for r in receipt['points']),
              'training_points': len(tuning['points']), 'training_shots': sum(r['shots'] for r in tuning['points']),
              'comparisons': comparisons,
              'hashes': {str(path.relative_to(rt.REPO)): rt.sha(path) for path in
                         [ROOT / 'plan.json', ROOT / 'selection.json', ROOT / 'verified.json',
                          confirmed / 'plan.json', confirmed / 'verified.json', ORIGINAL / 'source_points.json']},
              'claim_limit': 'Descriptive independent confirmation at 20 failures per point; no simultaneous superiority test. Compare damping within a channel. Binary BP uses X-only; Q-BP uses depolarizing p=1.5*p_X. Dense high-noise source grids dominate equal-rate averages; they are not pooled-shot estimates or thresholds. Paper ordinates describe ordinary undamped binary BP only.'}
    with (ROOT / 'results-table.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    rt.write_json(ROOT / 'assessment.json', result)
    return plan, groups, result


def plot(plan, groups):
    source = json.loads((ORIGINAL / 'source_points.json').read_text())
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharex=True, sharey=True)
    colors = {'binary_ms': '#2464a4', 'qbp_ms': '#24805a'}
    for ax, code in zip(axes.flat, sorted(plan['codes'], key=lambda c: plan['codes'][c]['d']), strict=True):
        c = plan['codes'][code]
        original = source['curves'][str(c['d'])]
        ax.plot([p['p'] for p in original], [p['block_ler_approx'] for p in original],
                color='#555555', linestyle=':', linewidth=1.1, label='Paper ordinary BP (approx.)')
        for family in ('binary_ms', 'qbp_ms'):
            for role in ('baseline', 'selected'):
                points = sorted(groups[code, family, role], key=lambda r: r['matched_x_rate'])
                label = ('BP, X-only' if family == 'binary_ms' else 'Q-BP, depolarizing')
                label += f', d={points[0]["decoder"]["v2c_damping"]:g}'
                x, y = [p['matched_x_rate'] for p in points], [p['rate'] for p in points]
                color = colors[family]
                ax.plot(x, y, '--' if role == 'baseline' else '-', color=color, linewidth=1.3,
                        marker='o' if role == 'selected' else None, markersize=2.5, label=label)
                ax.fill_between(x, [p['ci95_low'] for p in points], [p['ci95_high'] for p in points],
                                color=color, alpha=.07)
        ax.set_title(f'Toric [[{c["n"]},2,{c["d"]}]], T={c["n"]}')
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlim(.009, .12); ax.set_ylim(.0028, 1.15)
        ax.xaxis.set_major_locator(FixedLocator([.01, .02, .03, .05, .1]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda p, _: f'{p:g}'))
        ax.yaxis.set_major_locator(LogLocator(base=10))
        ax.yaxis.set_major_formatter(LogFormatterMathtext())
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
        ax.grid(which='major', alpha=.25); ax.grid(which='minor', axis='y', alpha=.1)
    for ax in axes[-1]:
        ax.set_xlabel(r'Matched X rate: BP $p=p_X$; Q-BP $p_{\mathrm{dep}}=1.5p_X$')
    for ax in axes[:, 0]:
        ax.set_ylabel('Block logical failure probability')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .96), ncol=3, frameon=False, fontsize=8.5)
    fig.suptitle('Roffe paper budgets: independent damping confirmation', y=.995, fontsize=13)
    fig.text(.5, .015, 'Fresh samples; 20 logical failures/point; shading: pointwise stopping-aware 95% intervals. Different decoder families use different channels.', ha='center', fontsize=8)
    fig.subplots_adjust(left=.08, right=.985, bottom=.105, top=.85, hspace=.25, wspace=.12)
    for ext in ('png', 'pdf'):
        fig.savefig(ROOT / f'damping-comparison.{ext}', dpi=190)
    plt.close(fig)


def main():
    plan, groups, result = assess()
    plot(plan, groups)
    lines = ['# Roffe: independent damping confirmation', '',
             'All 1,526 fixed-cohort tuning points and 436 fresh confirmation points are audited. Training retained 1,562,624 decoder shots. Confirmation retained 47,473 shots and 8,720 logical block failures; every point stopped at 20 failures. No new simulations are run by this report.', '',
             'Selection chose old-V2C weight d=0.5 for ordinary min-sum BP and d=0.3 for joint min-sum Q-BP on all four codes. Min-sum alpha_t=1-2^-t, fixed matched prior, float64 and paper T=n remain unchanged. Each source grid is preserved (25/28/28/28 rates).', '',
             'Damping helps Q-BP much more strongly than ordinary BP in this confirmation. Compare each damped decoder to its own undamped control: binary BP uses X-only noise; Q-BP uses depolarizing p=1.5*p_X. These families do not share a noise channel. The undamped ordinary-BP curve and its digitized paper comparison remain separate original evidence.', '',
             '![Independent damping results and approximate original ordinary-BP paper curves](damping-comparison.png)', '',
             'At matched X rate p_X=0.02 (binary physical p=0.02; Q-BP depolarizing physical p=0.03):', '',
             '| Code; paper T=n | BP LER d=0 → d=.5 | BP mean sweeps d=0 → d=.5 | Q-BP LER d=0 → d=.3 | Q-BP mean sweeps d=0 → d=.3 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['d']):
        c = plan['codes'][code]; values = []
        for family in ('binary_ms', 'qbp_ms'):
            a, b = [next(p for p in groups[code, family, role] if p['matched_x_rate'] == .02)
                    for role in ('baseline', 'selected')]
            values.extend([f'{a["rate"]:.5g} → {b["rate"]:.5g}',
                           f'{a["iterations"]/a["shots"]:.3g} → {b["iterations"]/b["shots"]:.3g}'])
        lines.append(f'| [[{c["n"]},2,{c["d"]}]]; {c["n"]} | ' + ' | '.join(values) + ' |')
    lines += ['', 'All source rates, equally weighted within each code (not pooled shots):', '',
              '| Code | Decoder | Mean LER d=0 → selected | Relative LER reduction | Mean sweeps d=0 → selected |',
              '| --- | --- | ---: | ---: | ---: |']
    for entry in result['comparisons']:
        a, b = entry['equal_rate_means']['baseline'], entry['equal_rate_means']['selected']
        lines.append(f'| {entry["code"]} | {entry["family"]} | {a["ler"]:.4g} → {b["ler"]:.4g} | {100*entry["ler_reduction_fraction"]:.1f}% | {a["iterations"]:.4g} → {b["iterations"]:.4g} |')
    lines += ['', 'Densely sampled high-noise rates near failure probability one dominate these equal-rate averages. They are descriptive summaries, not thresholds or evidence of uniform improvement at every rate. Twenty-failure intervals are broad; no simultaneous superiority criterion was prespecified.', '',
              'The complete 436-row results-table.csv retains pointwise exact stopping-aware 95% intervals, both work means, actual physical channels, source ordinary-BP ordinates for context, and ledger/summary hashes. assessment.json links both frozen plans, selected settings and audit receipts. Training is not pooled into confirmation. No OSD was run; this remains a canonical controlled adaptation.', '',
              'The automated final collector audited/normalized all results, then encountered duplicate paper metadata in the shared catalog. The catalog merger now permits identical paper records across studies and still rejects conflicting metadata. Revalidating the ledgers and refreshing the catalog from the completed audit repaired the display without rerunning simulations.']
    lines += ['', 'Paper BP-OSD reference: [all 108 Figure 3 BP+OSD-CS ordinates beside our confirmed results](../roffe-2005-07016-osd-comparison/RESULTS.md). The source table also preserves the unavailable length-450/p=.01 point, all four local arms, and separate OSD-0/CS threshold context.']
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'confirmation_points': result['confirmation_points'],
                      'confirmation_shots': result['confirmation_shots'],
                      'comparisons': result['comparisons']}, indent=2))


if __name__ == '__main__':
    main()
