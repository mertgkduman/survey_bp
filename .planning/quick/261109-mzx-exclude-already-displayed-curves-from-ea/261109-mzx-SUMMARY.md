---
quick_id: 261109-mzx
status: complete
date: 2026-11-09
implementation_commit: 1e6b825
verification: passed
---

# Add-curve picker excludes already displayed curves

Each plot's picker subtracts its visible curve identities from the eligible curves for its input, then applies prefix search. Reopening after addition excludes the newly displayed curve. Hidden curves remain addable and restore the existing entry without duplicates. Compare-all mode reports "All available curves are already displayed" when appropriate. Plot state remains independent.

Verification: 9 curve browser workflow groups and 7 public-results browser groups passed in Chromium with no page errors. Covered initial and repeated addition, keyboard/mouse restoration, compare-all empty state, safe empty keyboard handling, prefix/no-match behavior, same-input independent plots, tables/exports, imports, empty catalogs, stale selections, custom matrix/Stim, mobile and archived v1 loading. `node --check web/research/app.js` and `git diff --check` pass. No simulations or catalog rebuilds were needed.

Commands:
- `.venv/bin/python tests/research/browser_curves.py --url http://127.0.0.1:8876/web/research/ --output .git/research-picker-261109-mzx`
- `.venv/bin/python tests/research/browser_public_results.py --url http://127.0.0.1:8876/web/research/ --output .git/research-public-results-261109-mzx`

Source and documentation committed in `1e6b825`. User authorized committing and pushing to GitHub. GSD executed inline; scientific phase progress, model configuration, retained results, catalog and v1 bytes are unchanged.
