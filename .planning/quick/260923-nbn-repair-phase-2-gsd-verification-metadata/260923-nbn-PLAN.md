---
id: 260923-nbn
mode: quick
status: in_progress
depends_on: []
files_modified:
  - .planning/ROADMAP.md
  - .planning/config.json
  - .planning/STATE.md
  - .planning/phases/02-canonical-css-execution-and-policy-contracts/02-UAT.md
autonomous: true
must_haves:
  truths:
    - "Phase 2 has an equivalent one-line MVP user story without changing its scientific scope."
    - "GSD runs the repository's proven bounded-thread pytest command."
    - "UAT distinguishes the cumulative-descendant-count verifier defect from real per-plan task commits."
    - "Phase 2 remains verifying and is not reported complete while CR-01 through CR-04 remain unresolved."
  artifacts:
    - .planning/ROADMAP.md
    - .planning/config.json
    - .planning/STATE.md
    - .planning/phases/02-canonical-css-execution-and-policy-contracts/02-UAT.md
  key_links:
    - "workflow.test_command -> OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q"
    - "02-UAT.md commit reconciliation -> explicit summary task hashes in Git"
    - "STATE.md verification status -> 02-REVIEW.md unresolved findings"
---

# Repair Phase 2 GSD verification metadata

<objective>
Repair the Phase 2 GSD metadata without changing source code, result data, scientific scope, or scientific acceptance gates.

Purpose: Make the roadmap, test runner, UAT bookkeeping, and project state agree with the evidence already present in Git.
Output: Four narrowly edited planning/configuration artifacts; Phase 2 remains open for review-finding remediation.
</objective>

<guardrails>
- Do not modify source, tests, result data, Phase 2 summaries, or review/validation/security reports.
- Do not mark Phase 2 complete or reinterpret the 15 passing UAT checks as phase verification.
- Preserve every existing `model_overrides` and `effort.agent_overrides` entry exactly.
- Preserve all existing untracked files; do not stage, delete, move, or rewrite them.
- Do not inflate summary commit counts or hide a genuinely missing/non-ancestor task commit.
</guardrails>

<tasks>

<task type="auto">
  <name>Task 1: Normalize the Phase 2 MVP goal and project test command</name>
  <files>.planning/ROADMAP.md, .planning/config.json</files>
  <action>Replace only the Phase 2 Goal line with the equivalent one-line story: `As a researcher, I want to inspect and run a canonical binary BP policy composition, so that I can trust its outcomes and computational attribution.` Keep every Phase 2 requirement, success criterion, research focus, plan entry, and milestone boundary unchanged. Add `workflow.test_command` with the exact value `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`; make no other config change, especially to saved role models or reasoning efforts.</action>
  <verify>
    <automated>python -c 'import json,subprocess; p=".planning/config.json"; a=json.load(open(p)); b=json.loads(subprocess.check_output(["git","show","HEAD:"+p],text=True)); b["workflow"]["test_command"]="OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q"; assert a==b; r=open(".planning/ROADMAP.md").read(); assert "**Goal:** As a researcher, I want to inspect and run a canonical binary BP policy composition, so that I can trust its outcomes and computational attribution." in r'</automated>
  </verify>
  <done>The Phase 2 goal is a one-line MVP user story, and the only config delta is the exact bounded-thread pytest command.</done>
</task>

<task type="auto">
  <name>Task 2: Reconcile Phase 2 UAT commit bookkeeping from explicit hashes</name>
  <files>.planning/phases/02-canonical-css-execution-and-policy-contracts/02-UAT.md</files>
  <action>Re-audit each plan's explicitly attributed task hashes with `git cat-file -e` and `git merge-base --is-ancestor`. Record that the generated measurements 50, 47, 42, 30, 36, 24, 19, 14, and 6 count cumulative descendants from each moving `plan_head_before` through a later verification HEAD, so they are not per-plan commit counts. Replace those nine generated mismatch blockers with a reconciliation table retaining the summary counts 2, 4, 4, 5, 5, 4, 4, 6, and 4 for Plans 01-09. Keep the UAT session `status: complete` and its 15/15 results, but add an explicit phase-verification note that UAT completion does not complete Phase 2 and that `02-REVIEW.md` still reports four critical blockers and seven warnings. If any attributed hash is missing or not an ancestor at execution time, stop and retain a blocker naming that plan/hash rather than clearing it.</action>
  <verify>
    <automated>python -c 'from pathlib import Path; import subprocess; groups={"02-01":"c78493a 925e5e5","02-02":"a643c69 c594a15 914be06 7857a55","02-03":"df5807b 1a0de3b 9f46257 75e6929","02-04":"bc5a0df dbcc80d 99b30a0 b8acd43 7f14086","02-05":"d038dd1 59eed04 f01d5a7 eb2aed5 f408f12","02-06":"539d7ee a115841 1824eb4 ad0c881","02-07":"31ebaa0 636c5d9 74090e6 b9890e7","02-08":"2871426 3a26782 7edee78 f67cf05 5a31764 d315072","02-09":"e38ab89 c58c01d d173941 8754a19"}; [(subprocess.run(["git","cat-file","-e",h+"^{commit}"],check=True),subprocess.run(["git","merge-base","--is-ancestor",h,"HEAD"],check=True)) for hs in groups.values() for h in hs.split()]; t=Path(".planning/phases/02-canonical-css-execution-and-policy-contracts/02-UAT.md").read_text(); assert "commit_claim_mismatch" not in t; assert "cumulative-descendant" in t; assert "Phase 2 remains" in t and "CR-01" in t and "15" in t'</automated>
  </verify>
  <done>UAT records a defensible per-plan reconciliation, false cumulative-count blockers are gone, and unresolved scientific/code-review findings remain visible.</done>
</task>

<task type="auto">
  <name>Task 3: Make STATE truthful and run the configured full suite</name>
  <files>.planning/STATE.md</files>
  <action>Keep frontmatter `status: verifying`, change the Current Position label from execution to verification, and state that all nine Phase 2 plans and 15 UAT checks executed but Phase 2 is not complete because review findings CR-01 through CR-04 remain unresolved. Reconcile the executed-plan metric to 18 total across Phases 1 and 2, replace stale activity/next-step prose, and set the next remediation command to `$gsd-code-review 2 --fix`. Preserve all accumulated scientific decisions, open research concerns, roadmap scope, and the Phase 1 completion record. Run the configured full test command after the metadata edits; a passing suite does not override the review blockers.</action>
  <verify>
    <automated>OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q &amp;&amp; python -c 'import json; s=open(".planning/STATE.md").read(); r=open(".planning/ROADMAP.md").read(); c=json.load(open(".planning/config.json")); assert "status: verifying" in s and "— VERIFYING" in s and "CR-01" in s and "Total plans completed: 18" in s; assert "Phase complete — ready for verification" not in s; assert "- [ ] **Phase 2:" in r and "| 2. Canonical CSS Execution and Policy Contracts | 9/9 | In Progress" in r; assert c["workflow"]["test_command"]=="OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q"'</automated>
  </verify>
  <done>STATE consistently reports Phase 2 as verifying, points to review remediation, and the configured full suite passes without changing the phase-completion gate.</done>
</task>

</tasks>

<source_audit>
- GOAL: Covered by Tasks 1-3.
- REQ: No product requirement is added or changed; this quick task repairs metadata only.
- RESEARCH: None required; all target values are grounded in current project artifacts and Git history.
- CONTEXT: All fixed scope constraints are represented in task actions and guardrails.
</source_audit>

<success_criteria>
- Only the four declared metadata/configuration files differ from their pre-task tracked state.
- The exact configured test command passes.
- Phase 2 remains unchecked/In Progress in ROADMAP and `verifying` in STATE.
- UAT remains 15/15 complete while phase-level review blockers remain explicit.
- Existing untracked files and saved model/effort configuration are untouched.
</success_criteria>
