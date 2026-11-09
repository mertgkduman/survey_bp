---
quick_id: 261109-mzx
status: complete
---

# Exclude displayed curves from the add picker

Execute inline through gsd-quick. Scope: current v2 picker in web/research/app.js, browser_curves.py and affected browser_public_results.py assertions, interface documentation and task/state records.

1. Derive addable curves from current input's available curves minus the plot's visible curve identities, before prefix filtering. Hidden curves may be restored; selecting one clears hidden state without duplicate entries. Explain the all-displayed empty state.
2. Verify keyboard/mouse addition, re-open exclusion, hidden restoration, compare-all, prefix empty states and independent cards using both no-simulation Chromium suites. Update GSD records, commit and push main as requested.
