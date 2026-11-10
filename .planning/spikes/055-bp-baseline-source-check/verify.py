"""Verify the consistency of the dated citation/evidence shortlist, offline."""
from collections import Counter
import csv
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    papers = json.loads((root / 'papers.json').read_text())['papers']
    records = json.loads((root.parent / '054-bp-baseline-citation-screen/citation-records.json').read_text())['records']
    by_id = {r['id'].rsplit('/', 1)[-1]: r for r in records}
    assert len(by_id) == len(records) == len(papers)
    assert len({p['openalex_id'] for p in papers}) == len(papers)
    assert len({p['title'].casefold() for p in papers}) == len(papers)
    assert papers == sorted(papers, key=lambda p: (-p['citation_count'], p['title']))
    for p in papers:
        r = by_id[p['openalex_id']]
        assert p['citation_count'] == r['cited_by_count']
        assert p['title'] == r['title'] and p['publication_year'] == r['publication_year']
        assert p['citation_count'] > 0
        assert p['citation_record_url'] == 'https://api.openalex.org/works/' + p['openalex_id']
        assert p['paper_url'].startswith('https://')
        assert all(p[key] for key in ('authors', 'bp_rule', 'evidence_location', 'eligibility_evidence', 'edition_notes'))
    with (root / 'papers.csv').open(newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    assert csv_rows == [{key: str(value) for key, value in p.items()} for p in papers]
    kinds = Counter(p['classification'] for p in papers)
    assert kinds == {'direct_baseline': 12, 'code_benchmark': 2, 'hybrid_only': 2, 'specialized_min_sum': 1}
    report = {'status': 'passed', 'papers': len(papers), 'classifications': dict(kinds),
              'citations_match_snapshot': True, 'csv_matches_json': True,
              'primary_source_interpretation': 'manually checked at recorded evidence locations; not inferred by this consistency checker',
              'network_requests': 0, 'simulations': 0}
    (root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
