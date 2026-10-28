"""Assess the retained B2 p0=.15 policy on the fresh prior-confirmation seed."""

from __future__ import annotations

from hashlib import sha256
import json

from analyze_fixed import paired_p
from analyze_screen import _task_events
from runner import ROOT


def main() -> None:
    stage = "b2_prior_confirm"
    raw = (ROOT / f"{stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    result_raw = (ROOT / "results" / f"{stage}_results.json").read_bytes()
    result = json.loads(result_raw)
    if not result["complete"] or result["plan_sha256"] != sha256(raw).hexdigest():
        raise ValueError("complete audited B2 prior confirmation required")
    outcomes = {}
    for task in plan["tasks"]:
        if task["code"] != "b2":
            raise ValueError("unexpected code in B2 confirmation plan")
        _, failures, _ = _task_events(task, plan, sha256(raw).hexdigest())
        outcomes[task["candidate_id"]] = failures
    rows = {row["candidate_id"]: row for row in result["rows"]}
    incumbent_id = "sp_f64_v2_d01_p015_t5000"
    incumbent = rows[incumbent_id]
    old = outcomes[incumbent_id]
    comparisons = []
    for candidate_id in ("sp_f64_v2_d01_p014_t5000",
                         "sp_f64_v2_d01_p016_t5000",
                         "sp_f64_v2_d01_p017_t5000"):
        new = outcomes[candidate_id]
        rescues = sum(o and not n for o, n in zip(old, new, strict=True))
        losses = sum(n and not o for o, n in zip(old, new, strict=True))
        p = paired_p(rescues, losses)
        row = rows[candidate_id]
        comparisons.append({"candidate_id": candidate_id,
                            "failures": row["failures"], "shots": row["shots"],
                            "rescues_vs_retained": rescues,
                            "losses_vs_retained": losses,
                            "paired_improvement_p": p,
                            "below_retained_ci90": row["ler"] < incumbent["ci90_lower"],
                            "triggers_continued_prior_tuning":
                            p < .1 or row["ler"] < incumbent["ci90_lower"]})
    assessment = {"schema": "yao-bp4-tuning-b2-reselection-v1",
                  "stage_plan_sha256": sha256(raw).hexdigest(),
                  "stage_results_sha256": sha256(result_raw).hexdigest(),
                  "retained_candidate_id": incumbent_id,
                  "retained_failures": incumbent["failures"],
                  "retained_shots": incumbent["shots"],
                  "retained_ler": incumbent["ler"],
                  "retained_ci90": [incumbent["ci90_lower"], incumbent["ci90_upper"]],
                  "stop_in_tested_prior_neighborhood":
                  not any(c["triggers_continued_prior_tuning"] for c in comparisons),
                  "comparisons": comparisons}
    out = ROOT / "results/b2_reselection_assessment"
    out.with_suffix(".json").write_text(json.dumps(assessment, sort_keys=True, indent=2) + "\n")
    lines = ["# B2 prior reselection on a fresh paired seed", "",
             f"Retained `{incumbent_id}`: {incumbent['failures']}/{incumbent['shots']} "
             f"= {incumbent['ler']:.6g}; exact 90% interval "
             f"[{incumbent['ci90_lower']:.6g}, {incumbent['ci90_upper']:.6g}].", "",
             "| Neighbor | Failures/N | Rescues/losses | One-sided paired p | Continue? |",
             "|---|---:|---:|---:|---:|"]
    for c in comparisons:
        lines.append(f"| `{c['candidate_id']}` | {c['failures']}/{c['shots']} | "
                     f"{c['rescues_vs_retained']}/{c['losses_vs_retained']} | "
                     f"{c['paired_improvement_p']:.4g} | "
                     f"{'yes' if c['triggers_continued_prior_tuning'] else 'no'} |")
    lines.extend(["", "Stop in this tested prior neighborhood: " +
                  ("yes" if assessment["stop_in_tested_prior_neighborhood"] else "no"), "",
                  "The p-values are unadjusted after sequential policy search."])
    out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(assessment["stop_in_tested_prior_neighborhood"])


if __name__ == "__main__":
    main()
