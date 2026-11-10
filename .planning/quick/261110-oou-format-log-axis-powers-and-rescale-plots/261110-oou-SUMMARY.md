---
quick_id: 261110-oou
status: complete
date: 2026-11-10
implementation_commit: 8d35f04
verification: passed
---

# Logarithmic axis labels and curve visibility

Failure-rate plots label each power of ten with a raised SVG exponent. Lighter gridlines mark multiples 2 through 9 within each decade.

Toggling curves refits both axes to the displayed observations and their confidence intervals. The x-axis channel mode follows the visible curves. Hover previews are clipped to the fitted plot area. When every curve is hidden, the selected curves supply the preview scales.

Chromium passed 10 curve workflow checks and 7 public results checks. The tests verify raised exponents, minor gridlines, matching axis limits for the decoder selector and curve toggles, mixed-channel conversion, all-hidden previews, and the existing results workflows. Five plot-coordinate tests passed. The rendered B1 chart was inspected at the two-plot layout size.

- `.venv/bin/python tests/research/browser_curves.py --url http://127.0.0.1:8876/web/research/ --output .git/research-log-axis-261110-oou-final`
- `.venv/bin/python tests/research/browser_public_results.py --url http://127.0.0.1:8876/web/research/ --output .git/research-public-results-261110-oou`
- `.venv/bin/python -m pytest tests/research/test_plot_coordinates.py -q`
- `node --check web/research/app.js`
- `git diff --check`
