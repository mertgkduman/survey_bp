---
quick_id: 261110-lsd
status: complete
date: 2026-11-10
implementation_commit: 7b8e702
verification: passed
---

# Request experiment results from a validated builder configuration

Added **Request experiment results** beside **Download experiment package**. It shares the existing validation gate and clears its prepared request on edits, reset, input refresh or failed validation.

The static workbench has no job-submission service. The action prepares a review panel with a downloadable complete portable specification and a prefilled GitHub issue link. The user attaches the JSON and submits the issue on GitHub. Request preparation does not submit a job, issue or measured results. Registered codes materialize exact matrices using the same path as package export; custom matrices, Stim text, per-point budgets and provenance remain complete in the attachment. The draft contains a SHA-256 of the exact downloadable bytes and a compact summary, so long inputs do not overflow its URL. Async materialization is cancelled by a configuration-generation change to prevent a stale request returning after edits.

Verification: **5 request browser workflow groups + 7 public-results browser groups passed**, no page errors, no simulations and no issues submitted. Request navigation was intercepted at the browser-context level. Covered initial disabled state, post-validation activation, accessible focus/expanded state, complete BB72 matrices, exact SHA-256 and byte-identical request/package specification, invalid/edited/reset states, delayed-input races, long custom Stim, full JSON mode, failed input fetches, mobile width, import/empty/stale-input regression and archived v1 load. Python validate_experiment checked downloaded code/circuit inputs without sampling. Node syntax and diff checks passed.

Commands:
- `PYTHONPATH=src .venv/bin/python tests/research/browser_requests.py --output .git/research-requests-261110-lsd-2`
- `.venv/bin/python tests/research/browser_public_results.py --url http://127.0.0.1:8876/web/research/ --output .git/research-public-results-261110-lsd`
- `node --check web/research/app.js`
- `git diff --check`

GitHub's official [attachment documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files) was checked for JSON support. No external issue was created. Companion JSON files record browser checks. Backend execution, retained evidence, catalogs, model configuration, archived v1 and scientific phase progress are unchanged.

Executed inline through gsd-quick. Implementation: `7b8e702`.
