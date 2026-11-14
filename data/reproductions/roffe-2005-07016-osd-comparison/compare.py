"""Extract the paper's Figure3 BP-OSD values and join existing confirmed results."""
import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ORIGINAL = ROOT.with_name('roffe-2005-07016-bp')
DAMPING = ROOT.with_name('roffe-2005-07016-damping')
ARCHIVE_SHA = 'e68595d13a330c067e280a473354d7254816bea8be2746ae4a5ab46557a23ef4'
FIGURE_SHA = '547fb722746f75e26bd1913c9a67b45ca7d29df9b48f7ed4d2554eaefbe63733'
COLORS = {'1.000000,0.000000,0.000000': 9, '0.000000,0.000000,1.000000': 11,
          '0.000000,0.501961,0.000000': 13, '0.501961,0.000000,0.501961': 15}
VERTICES = re.compile(r'\\pgfpath(?:move|line)to\{\\pgfqpoint\{([\d.-]+)in\}\{([\d.-]+)in\}\}')
COLOR = re.compile(r'\\definecolor\{currentstroke\}\{rgb\}\{([^}]+)\}')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probability(y):
    return 10**((y-2.716649)/(.458176/2))


def extract_figure(figure):
    """Main-panel paths only: inset curves have fewer than20 vertices."""
    if sha256(figure).hexdigest() != FIGURE_SHA:
        raise ValueError('source vector figure differs from the qualified revision')
    blocks = figure.decode().split('\\begin{pgfscope}')
    bars = {d: [] for d in COLORS.values()}
    for block in blocks:
        points, color = VERTICES.findall(block), COLOR.search(block)
        if len(points) == 2 and color and color.group(1) in COLORS and points[0][0] == points[1][0]:
            bars[COLORS[color.group(1)]].append(tuple(map(float, (points[0][0], points[0][1], points[1][1]))))
    curves = {'bp': {}, 'bp_osd_cs': {}}
    for block in blocks:
        vertices, color = VERTICES.findall(block), COLOR.search(block)
        if len(vertices) < 20 or not color or color.group(1) not in COLORS:
            continue
        if '\\pgfsetdash{{3.700000pt}{1.600000pt}}' in block:
            kind = 'bp'
        elif '\\pgfsetdash{}{0pt}' in block:
            kind = 'bp_osd_cs'
        else:
            raise ValueError('unknown source curve line style')
        distance = COLORS[color.group(1)]
        if str(distance) in curves[kind]:
            raise ValueError('duplicate source curve; possible inset contamination')
        points = []
        for xs, ys in vertices:
            x, y = float(xs), float(ys)
            matches = [(min(lo, hi), max(lo, hi)) for bx, lo, hi in bars[distance]
                       if abs(x-bx) < 1e-7 and min(lo, hi)-1e-6 <= y <= max(lo, hi)+1e-6]
            if len(matches) != 1:
                raise ValueError('source vertex has no unique measured vertical error bar')
            raw = 10**(-2+(x-.869111)/(3.046496-.869111))
            p = round(raw, 6)
            if abs(raw-p) > 1e-7:
                raise ValueError('source rate is outside its displayed decimal grid')
            points.append({'p': p, 'block_ler_approx': probability(y), 'x_inches': x, 'y_inches': y,
                           'drawn_errorbar_low_approx': probability(matches[0][0]),
                           'drawn_errorbar_high_approx': probability(matches[0][1])})
        curves[kind][str(distance)] = points
    expected = {'bp': {'9': 25, '11': 28, '13': 28, '15': 28},
                'bp_osd_cs': {'9': 25, '11': 28, '13': 28, '15': 27}}
    if {kind: {d: len(p) for d, p in values.items()} for kind, values in curves.items()} != expected:
        raise ValueError('unexpected main-panel curve inventory')
    for distance, points in curves['bp'].items():
        a = {p['p'] for p in points}; b = {p['p'] for p in curves['bp_osd_cs'][distance]}
        if not b <= a or a-b != ({.01} if distance == '15' else set()):
            raise ValueError('unexpected BP/BP-OSD rate mismatch')
    return curves


def extract(archive):
    if digest(archive) != ARCHIVE_SHA:
        raise ValueError('source archive differs from the pinned arXiv v2 artifact')
    with tarfile.open(archive) as tar:
        figure = tar.extractfile('toric_threshold.pgf').read()
        tex = tar.extractfile('hgp_bp_osd_paper.tex').read()
    curves = extract_figure(figure)
    old = json.loads((ORIGINAL / 'source_points.json').read_text())
    # Independent extraction must reproduce every previously frozen BP vertex.
    for distance, points in curves['bp'].items():
        assert [{k: p[k] for k in ('p', 'block_ler_approx', 'x_inches', 'y_inches')} for p in points] == old['curves'][distance]
    assert b'\\lambda=60' in tex
    return {'schema': 'roffe-figure3-bp-osd-source-v1', 'paper': 'https://arxiv.org/abs/2005.07016v2',
            'source_url': 'https://arxiv.org/src/2005.07016v2', 'source_archive_sha256': digest(archive),
            'figure_member': 'toric_threshold.pgf', 'figure_sha256': sha256(figure).hexdigest(),
            'tex_member': 'hgp_bp_osd_paper.tex', 'tex_sha256': sha256(tex).hexdigest(),
            'source_decoder': 'BP+OSD-CS', 'combination_sweep_lambda': 60,
            'bp_iteration_cap': 'code block length n', 'source_channel': 'x_only',
            'coordinate_status': 'approximate main-panel vector ordinates, each matched to a drawn vertical error bar',
            'source_sample_counts': None, 'source_work_means': None, 'source_errorbar_confidence_level': None,
            'missing_points': [{'distance': 15, 'physical_p': .01, 'status': 'not_plotted; no interpolation, zero, or upper bound inferred'}],
            'x_log10_calibration': {'p_001_x': .869111, 'p_01_x': 3.046496},
            'y_log10_calibration': {'rate_1_y': 2.716649, 'inches_per_two_decades': .458176},
            'curves': curves}


def join(source, receipt):
    index = {(r['code'], r['base_arm'], r['role'], r['matched_x_rate']): r for r in receipt['points']}
    if len(index) != len(receipt['points']) or len(index) != 436:
        raise ValueError('confirmation inventory differs from four measured arms per source rate')
    rows = []
    for distance in (9, 11, 13, 15):
        osd = {p['p']: p for p in source['curves']['bp_osd_cs'][str(distance)]}
        for bp in source['curves']['bp'][str(distance)]:
            p, code = bp['p'], f'toric{distance}'
            target = osd.get(p)
            row = {'code': code, 'n': 2*distance**2, 'distance': distance, 'x_only_physical_p': p,
                   'paper_bp_ler_approx': bp['block_ler_approx'],
                   'paper_bp_osd_cs_ler_approx': target['block_ler_approx'] if target else None,
                   'paper_bp_osd_cs_lambda': 60, 'paper_bp_osd_cs_status': 'source_vector_approximation' if target else 'not_plotted',
                   'paper_bp_osd_cs_shots': None, 'paper_bp_osd_cs_mean_iterations': None,
                   'paper_bp_osd_cs_mean_directed_edge_updates': None,
                   'paper_drawn_errorbar_low_approx': target['drawn_errorbar_low_approx'] if target else None,
                   'paper_drawn_errorbar_high_approx': target['drawn_errorbar_high_approx'] if target else None,
                   'paper_errorbar_confidence_level': None, 'bp_iteration_cap': 2*distance**2,
                   'qbp_depolarizing_physical_p': 1.5*p}
            for family, prefix in [('binary_ms', 'bp'), ('qbp_ms', 'qbp')]:
                for role, suffix in [('baseline', 'undamped'), ('selected', 'damped')]:
                    r = index[code, family, role, p]
                    expected = p if family == 'binary_ms' else 1.5*p
                    assert r['physical_p'] == expected and r['decoder']['max_iterations'] == row['n']
                    assert r['decoder']['v2c_damping'] == (0. if role == 'baseline' else .5 if family == 'binary_ms' else .3)
                    label = prefix + '_' + suffix
                    row.update({label+'_ler': r['rate'], label+'_shots': r['shots'],
                                label+'_ci95_low': r['ci95_low'], label+'_ci95_high': r['ci95_high'],
                                label+'_mean_iterations': r['iterations']/r['shots'],
                                label+'_mean_directed_edge_updates': r['directed_edge_updates']/r['shots'],
                                label+'_summary_sha256': r['summary_sha256']})
            row['bp_damped_ler_over_paper_osd_cs'] = row['bp_damped_ler']/target['block_ler_approx'] if target else None
            rows.append(row)
    return rows


def number(value):
    if value is None:
        return 'not plotted'
    if value and (abs(value) < .001 or abs(value) >= 10000):
        exponent = math.floor(math.log10(abs(value)))
        return f'${value/10**exponent:.4g}\\times10^{{{exponent}}}$'
    return f'{value:.4g}'


def markdown_table(rows):
    lines = ['| X rate p | Paper BP≈ | Paper BP+OSD-CS≈ | BP d=0 | BP d=.5 | Q-BP d=0, dep. 1.5p | Q-BP d=.3, dep. 1.5p |',
             '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| ' + ' | '.join([f'{r["x_only_physical_p"]:g}'] + [number(r[key]) for key in
                     ['paper_bp_ler_approx', 'paper_bp_osd_cs_ler_approx', 'bp_undamped_ler', 'bp_damped_ler',
                      'qbp_undamped_ler', 'qbp_damped_ler']]) + ' |')
    return lines


def plot(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.6), sharex=True, sharey=True)
    for ax, distance in zip(axes.flat, (9, 11, 13, 15), strict=True):
        points = [r for r in rows if r['distance'] == distance]
        styles = [('paper_bp_ler_approx', 'Paper BP, X-only', '#777777', ':'),
                  ('paper_bp_osd_cs_ler_approx', r'Paper BP+OSD-CS, X-only, $\lambda=60$', '#c33e32', '-'),
                  ('bp_undamped_ler', 'Our BP d=0, X-only', '#2464a4', '--'),
                  ('bp_damped_ler', 'Our BP d=.5, X-only', '#2464a4', '-'),
                  ('qbp_undamped_ler', 'Our Q-BP d=0, depolarizing', '#24805a', '--'),
                  ('qbp_damped_ler', 'Our Q-BP d=.3, depolarizing', '#24805a', '-')]
        for key, label, color, style in styles:
            visible = [r for r in points if r[key] is not None]
            ax.plot([r['x_only_physical_p'] for r in visible], [r[key] for r in visible], linestyle=style,
                    color=color, linewidth=1.3, marker='o' if key == 'paper_bp_osd_cs_ler_approx' else None,
                    markersize=2.5, label=label)
        for prefix in ('bp_damped', 'qbp_damped'):
            ax.fill_between([r['x_only_physical_p'] for r in points], [r[prefix+'_ci95_low'] for r in points],
                            [r[prefix+'_ci95_high'] for r in points], color='#2464a4' if prefix.startswith('bp_') else '#24805a', alpha=.08)
        ax.set_title(f'Toric [[{2*distance**2},2,{distance}]], BP cap T={2*distance**2}')
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(.009, .12); ax.set_ylim(8e-10, 1.2)
        ax.xaxis.set_major_locator(FixedLocator([.01, .02, .03, .05, .1]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda p, _: f'{p:g}'))
        ax.yaxis.set_major_locator(FixedLocator([10**exponent for exponent in range(-9, 1)]))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'$10^{{{round(math.log10(value))}}}$'))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
        ax.grid(which='major', alpha=.25); ax.grid(which='minor', axis='y', alpha=.08)
    for ax in axes[-1]:
        ax.set_xlabel(r'X rate $p$; Q-BP depolarizing rate $1.5p$')
    for ax in axes[:, 0]:
        ax.set_ylabel('Block logical failure probability')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .96), ncol=2, frameon=False, fontsize=8.5)
    fig.suptitle('Roffe Figure 3 BP-OSD reference and confirmed BP-family results', y=.995, fontsize=12)
    fig.text(.5, .015, 'Paper ordinates approximate; local shading: pointwise 95% intervals. OSD adds postprocessing work. Q-BP uses a different channel.', ha='center', fontsize=8)
    fig.subplots_adjust(top=.81, bottom=.1, left=.085, right=.985, hspace=.25, wspace=.13)
    for extension in ('png', 'pdf'):
        fig.savefig(ROOT / f'comparison.{extension}', dpi=190)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=REPO / '.git/roffe-source/source.tar')
    args = parser.parse_args()
    source = extract(args.archive)
    receipt_path = DAMPING / 'confirmation/verified.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['plan_sha256'] == digest(DAMPING / 'confirmation/plan.json')
    rows = join(source, receipt)
    (ROOT / 'source_points.json').write_text(json.dumps(source, indent=2, sort_keys=True)+'\n')
    with (ROOT / 'comparison-table.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    assessment = {'schema': 'roffe-bp-osd-context-comparison-v1', 'rows': len(rows),
                  'paper_osd_points': sum(r['paper_bp_osd_cs_ler_approx'] is not None for r in rows),
                  'matched_confirmation_measurements': len(receipt['points']),
                  'paper_osd_per_distance': {d: len(p) for d, p in source['curves']['bp_osd_cs'].items()},
                  'missing_source_values': source['missing_points'],
                  'source_archive_sha256': source['source_archive_sha256'], 'figure_sha256': source['figure_sha256'],
                  'confirmation_receipt_sha256': digest(receipt_path),
                  'comparison_scope': 'direct X-only BP versus source X-only BP+OSD-CS; Q-BP depolarizing shown as different-channel context',
                  'work_scope': 'BP cap T=n in all arms; source OSD adds elimination/candidate search, author work means/counts unavailable',
                  'at_x_rate_002': [{key: r[key] for key in ['code', 'paper_bp_osd_cs_ler_approx', 'bp_undamped_ler',
                                           'bp_damped_ler', 'qbp_damped_ler', 'bp_damped_ler_over_paper_osd_cs']}
                                     for r in rows if r['x_only_physical_p'] == .02]}
    (ROOT / 'assessment.json').write_text(json.dumps(assessment, indent=2, sort_keys=True)+'\n')
    plot(rows)
    lines = ['# Roffe Figure 3: BP-OSD and confirmed BP-family comparison', '',
             'All 108 plotted BP+OSD-CS points for the four toric codes are included below, together with all 109 ordinary-BP source points and 436 independent confirmation measurements. Values marked paper are approximate ordinates extracted from the original vector source, not locally rerun BP-OSD experiments. Every extracted vertex matches a drawn vertical error bar; author sample counts, error-bar confidence convention and work means remain unavailable.', '',
             'Source: [Roffe et al., arXiv:2005.07016v2](https://arxiv.org/abs/2005.07016v2), Figure 3, Section V/VI and Appendix C. BP+OSD-CS uses combination-sweep depth lambda=60 after nonconvergent min-sum BP, with BP capped at T=n. Lambda=60 is the search-depth parameter, not 60 OSD iterations. Elimination and candidate search add work beyond that BP cap; source work cannot be equated to our measured BP sweeps or directed edge updates.', '',
             'Paper BP/BP+OSD-CS and our binary BP are X-only at physical p. Our Q-BP is joint-Pauli depolarizing at 1.5p, so it is contextual and not a same-channel decoder ranking. Our d=0 and selected-damping arms use fresh confirmation samples and 20 logical failures per point; confidence intervals and both mean work measures are in comparison-table.csv. No source/local evidence is pooled and no missing ordinate is interpolated.', '',
             '![BP-OSD source reference and confirmed BP-family curves](comparison.png)', '',
             'At p=0.02 for X-only methods (Q-BP depolarizing p=0.03):', '',
             '| Code | Paper BP+OSD-CS≈ | Our BP d=0 | Our BP d=.5 | Our Q-BP d=.3, depolarizing | BP d=.5 LER / paper BP-OSD LER |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if r['x_only_physical_p'] == .02:
            lines.append(f'| [[{r["n"]},2,{r["distance"]}]] | ' + ' | '.join(number(r[k]) for k in
                         ['paper_bp_osd_cs_ler_approx', 'bp_undamped_ler', 'bp_damped_ler', 'qbp_damped_ler', 'bp_damped_ler_over_paper_osd_cs']) + ' |')
    lines += ['', 'The paper BP+OSD-CS LER at this rate is about 2,200 to 1.2 million times lower than our damped binary BP point estimates, with the largest gaps on larger codes. The OSD benefit is much larger than the damping benefit at low physical error rates. This compares logical performance, not equal total computational work. Even the smaller Q-BP point estimates remain well above the paper OSD curve here, but their different channel prevents attributing that numerical gap solely to decoder choice.', '',
              'The length-450 code has no plotted BP-OSD value at p=0.01. It is explicitly unavailable below; we infer neither zero failures nor an upper bound.', '',
              'Other paper summary results (Table III; percentages, different code families):', '',
              '| Code family | BP threshold | BP+OSD-0 threshold | BP+OSD-CS threshold |',
              '| --- | ---: | ---: | ---: |',
              '| Toric | not observed | 9.2 ± 0.2% | 9.9 ± 0.2% |',
              '| Semi-topological | not observed | 9.1 ± 0.2% | 9.7 ± 0.2% |',
              '| Random | 6.5 ± 0.1% | 6.7 ± 0.1% | 7.1 ± 0.1% |', '',
              'Those OSD-0 thresholds do not supply per-code OSD-0 LER curves. Figure 6 separately compares OSD-E lambda=12 with OSD-CS lambda=86 on distance15; its settings are distinct from the Figure3 lambda60 curves tabulated here. Figures4/5 concern other codes without current local comparison runs and are outside this four-code table.', '',
              'All Figure3 rates and available source points follow. Each table is sorted by its original source grid. A single CSV contains these109 rows, source error-bar geometry (confidence unspecified), all436 local shot counts/95% intervals, both work means and summary hashes.']
    for distance in (9, 11, 13, 15):
        points = [r for r in rows if r['distance'] == distance]
        lines += ['', f'## [[{2*distance**2},2,{distance}]], BP cap T={2*distance**2}', '', *markdown_table(points)]
    lines += ['', 'New local lower-cost methods: [canonical BP + OSD-0 / CS-10 results and separate work accounting](../roffe-2005-07016-osd-fast/RESULTS.md). Pending points remain explicitly unavailable until their audited runs finish.']
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(assessment, indent=2))


if __name__ == '__main__':
    main()
