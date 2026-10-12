# Phase 9 CSS evaluation evidence

The [Phase 9 evidence index](../data/results/phase9-css-evidence-index-v1.json) binds fourteen selected source variants, the bounded Yao B1 adaptation, and three controlled comparisons to retained receipts. It distinguishes source qualification from project-owned canonical execution. All controlled results below are small, bounded explorations; none establishes decoder superiority or source-faithful curve reproduction.

The index records `phase_status=complete` and `eval03_complete=true` because all three prospectively frozen positive matched sample sets and the required Phase 9 receipt gates are complete. It records no phase-execution blocker. Its source and publication limitations below remain open facts for later work; the censored Yao tracer did not pass its paper target.
The literal source-execution and published-curve capabilities in EVAL-01 and EVAL-02 remain pending in `REQUIREMENTS.md` until exact author artifacts/settings and a qualifying assessment exist.

## Source and target status

- Yao Figure 3 `bpgd-t001`, B1 p=0.10 has an [authored target receipt](../data/studies/phase9-yao-b1-t001-p010-source-target-v1.json) at 0.855932 and a frozen 100-failure inverse-binomial design. The [verified adaptation assessment](../data/studies/phase9-yao-b1-t001-p010-v4-assessment.json) stopped at the 1,800 second wall cap after two sealed timeout terminals. Its status is `inconclusive_cap_censored`; no `T_100`, interval, estimated source rate, or target verdict exists. The frozen all-shot outcome matrix counts timeout as failure, but these administrative terminals do not estimate the paper-style logical error rate. Earlier zero-credit diagnostics remain linked in the assessment. The project B1 artifact has a project-derived logical basis; exact ordered paper-artifact and author-code identities remain unverified.
- Bhatnagar Figure 5 source numeric points are unavailable in this workspace. The [qualification receipt](../literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/source-qualification-v1.json) records a later author-data route or a pinned two-pass digitization route. Neither has supplied a target assessment.
- Rabeti Figure 5 has [authored target coordinates](../literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/source-targets-v1.json), but the source digest discrepancy and maximal-subtree ensemble identity remain unresolved. The list/vote control below tests a declared two-member adaptation and is separate from a source-curve assessment.

Exact failure-count stopping uses the ordinal of the target-th failure only if it is reached. A whole terminal batch may retain an authorized tail, but that tail cannot enter the inverse-binomial interval. A cap-censored run has no inferential prefix and no factor-1.5 verdict. The factor applies only to the frozen Yao tracer, not to a journal-wide reproduction tolerance.

## Controlled comparisons

Each family used its own [measured profile and frozen design](../data/studies/phase9-controlled-design-v2.json). Calibration samples are disjoint from evaluative samples. Every physical sample was delivered to every declared arm. The public merge and report were independently verified. All-shot, conditional-acceptance, and acceptance-probability views remain separate in the study receipts; zero accepted shots produce an unavailable conditional rate with a reason.

| Family and receipt | Frozen/completed matched samples | Paired all-shot result | Actual C2V updates | Interpretation |
| --- | ---: | --- | --- | --- |
| [Flooding vs serial schedule](../data/studies/phase9-update-schedule-control-v1.json) | 3/3 | 3 joint failures, 0 discordant; risk difference 0, interval [-0.7679, 0.7679] | flooding 7,938; serial 3,996 | Both arms had zero accepted terminals under tight work caps; conditional failure rates are unavailable. |
| [Initial BP vs Relay and Beam](../data/studies/phase9-relay-beam-control-v2.json) | 16/16 | Each contrast: 8 joint successes, 8 joint failures, 0 discordant; risk difference 0, interval [-0.2396, 0.2396] | 34,476 combined, including common initial BP once | Two baseline contrasts enter one Holm family; neither is rejected. |
| [MBBP list vs vote](../data/studies/phase9-mbbp-list-vote-control-v1.json) | 2/2 | 2 joint successes, 0 discordant; risk difference 0, interval [-0.8882, 0.8882] | 24 combined, with the two members charged once per sample | One retained member set feeds both decisions; the one-contrast family is not rejected. |

The [schedule report](../data/results/phase9-controlled-evaluation-v1/schedule/report/controlled-ordinary-assessment.json) stores typed convergence, iteration, work, runtime, process-scope RSS, and evidence/storage leaves for every arm. A work-budget terminal can have unavailable convergence with an explicit reason. The [Relay/Beam report](../data/results/phase9-controlled-evaluation-v2/relay_beam/report/controlled-relay_beam-assessment.json) and [MBBP report](../data/results/phase9-controlled-evaluation-v1/mbbp_list_vote/report/controlled-mbbp_list_vote-assessment.json) separate shared computation, continuation or decision work, and independent validation. MBBP member iterations are unavailable from the canonical terminal and remain typed unavailable; they are never filled with zero. The first Relay/Beam result version is retained only as a diagnostic because one no-candidate terminal had charged an original check that did not run. The version-two report corrects that cost and is the assessed result.

## Public commands

Run from the project root with the checked-in environment. The commands below inspect or replay retained evidence. `plan` and `run-local` are available for a new frozen study; the retained roots are already complete.

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli preflight \
  --campaign data/results/phase9-yao-b1-t001-p010-v4/campaign.json --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli verify \
  --plan data/results/phase9-yao-b1-t001-p010-v4/plan/failure-count-plan.json \
  --merge data/results/phase9-yao-b1-t001-p010-v4/merge/failure-count-merge.json \
  --report data/results/phase9-yao-b1-t001-p010-v4/assessment/failure-count-assessment.json \
  --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli verify \
  --plan data/results/phase9-controlled-design-v1/schedule/plan/campaign-ordered-plan.json \
  --merge data/results/phase9-controlled-evaluation-v1/schedule/merge/campaign-ordered-merge.json \
  --report data/results/phase9-controlled-evaluation-v1/schedule/report/controlled-ordinary-assessment.json \
  --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli verify \
  --plan data/results/phase9-controlled-design-v2/relay_beam/plan/campaign-ordered-plan.json \
  --merge data/results/phase9-controlled-evaluation-v2/relay_beam/merge/controlled-relay_beam-merge.json \
  --report data/results/phase9-controlled-evaluation-v2/relay_beam/report/controlled-relay_beam-assessment.json \
  --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli verify \
  --plan data/results/phase9-controlled-design-v1/mbbp_list_vote/plan/campaign-ordered-plan.json \
  --merge data/results/phase9-controlled-evaluation-v1/mbbp_list_vote/merge/controlled-mbbp_list_vote-merge.json \
  --report data/results/phase9-controlled-evaluation-v1/mbbp_list_vote/report/controlled-mbbp_list_vote-assessment.json \
  --campaign-root .
```

Frozen inputs for new public `plan` calls are [Yao B1](../data/results/phase9-yao-b1-t001-p010-v4/campaign.json), [schedule](../data/studies/phase9-control-schedule-ordered-work-v1.json), [Relay/Beam](../data/studies/phase9-control-relay_beam-ordered-work-v2.json), and [MBBP list/vote](../data/studies/phase9-control-mbbp_list_vote-ordered-work-v1.json). Public `run-local`, `merge`, `resume`, and `assess` accept their frozen plan and retained receipt paths. The [campaign guide](campaigns.md) defines their arguments and partial-group behavior. A public list/vote decision is declared by the MBBP policy and represented by its shared-member receipt; it does not supply the paper's unresolved ensemble.

## Open external facts

Author implementations and exact ordered experiment artifacts need later digest-bound qualification. Journal-grade reproduction tolerance is unset beyond the one B1 tracer's prespecified factor. HPC site wall, core, memory, storage, and accounting ceilings are not available; resource values above are measured local evidence. Publication Slurm authorization remains `deny`.
