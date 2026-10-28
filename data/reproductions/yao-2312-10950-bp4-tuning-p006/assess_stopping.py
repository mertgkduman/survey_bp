"""Apply the prespecified finite-neighborhood 90% stopping rule on holdout shots."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json

from analyze_fixed import paired_p
from analyze_screen import _task_events
from runner import ROOT


INCUMBENTS = {"a5": "sp_f64_v2_d01_p006_t1000",
              "b2": "sp_f64_v2_d01_p015_t100"}


def main(stage: str = "validate") -> None:
    if stage not in {"validate", "followup", "joint_final", "a5_prior", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood", "b2_prior_confirm"}:
        raise ValueError("unknown stopping-assessment stage")
    result_path = ROOT / "results" / f"{stage}_results.json"
    result = json.loads(result_path.read_text())
    if not result["complete"] or result["stage"] != stage:
        raise ValueError("complete audited fixed-shot result required")
    raw = (ROOT / f"{stage}_plan.json").read_bytes()
    plan = json.loads(raw)
    plan_sha = sha256(raw).hexdigest()
    if result["plan_sha256"] != plan_sha:
        raise ValueError("holdout assessment and plan differ")
    incumbents = INCUMBENTS if stage == "validate" else plan["incumbents"]
    rows = {(r["code"], r["candidate_id"]): r for r in result["rows"]}
    outcomes = {}
    for task in plan["tasks"]:
        _, failures, _ = _task_events(task, plan, plan_sha)
        outcomes[(task["code"], task["candidate_id"])] = failures
    codes = {}
    code_names = tuple(plan["points"])
    lines = [f"# BP4 p=.06 {stage} stopping assessment", "",
             "The code-specific incumbents were frozen in the study plan before this stage's samples:",
             "; ".join(f"{code.upper()}: `{incumbents[code]}`" for code in code_names) + ".",
             "A tested neighbor triggers more tuning if its observed LER falls below the incumbent's",
             "exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.",
             "This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.", ""]
    for code in code_names:
        incumbent_id = incumbents[code]
        incumbent = rows[(code, incumbent_id)]
        old = outcomes[(code, incumbent_id)]
        comparison = []
        for candidate_id in plan["points"][code]["candidate_ids"]:
            if candidate_id == incumbent_id:
                continue
            candidate = rows[(code, candidate_id)]
            new = outcomes[(code, candidate_id)]
            rescues = sum(o and not n for o, n in zip(old, new, strict=True))
            losses = sum(n and not o for o, n in zip(old, new, strict=True))
            p = paired_p(rescues, losses)
            better_outside = candidate["ler"] < incumbent["ci90_lower"]
            paired_evidence = p < .1
            comparison.append({"candidate_id": candidate_id, "failures": candidate["failures"],
                               "shots": candidate["shots"], "ler": candidate["ler"],
                               "rescues_vs_incumbent": rescues, "losses_vs_incumbent": losses,
                               "paired_improvement_p": p, "below_incumbent_ci90": better_outside,
                               "triggers_continued_tuning": better_outside or paired_evidence})
        triggers = [r["candidate_id"] for r in comparison if r["triggers_continued_tuning"]]
        codes[code] = {"incumbent_id": incumbent_id,
                       "incumbent_failures": incumbent["failures"],
                       "incumbent_shots": incumbent["shots"],
                       "incumbent_ler": incumbent["ler"],
                       "incumbent_ci90": [incumbent["ci90_lower"], incumbent["ci90_upper"]],
                       "stop_in_tested_neighborhood": not triggers,
                       "continued_tuning_triggers": triggers, "comparisons": comparison}
        lines.extend([f"## {code.upper()}", "",
                      f"Incumbent: `{incumbent_id}`, {incumbent['failures']}/{incumbent['shots']} "
                      f"= {incumbent['ler']:.6g}; 90% CI "
                      f"[{incumbent['ci90_lower']:.6g}, {incumbent['ci90_upper']:.6g}].", "",
                      "| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |",
                      "|---|---:|---:|---:|---:|"])
        for r in sorted(comparison, key=lambda x: x["failures"]):
            lines.append(f"| {r['candidate_id']} | {r['failures']}/{r['shots']} | "
                         f"{r['rescues_vs_incumbent']}/{r['losses_vs_incumbent']} | "
                         f"{r['paired_improvement_p']:.4g} | "
                         f"{'yes' if r['triggers_continued_tuning'] else 'no'} |")
        lines.extend(["", "Stop under the stated rule: " + ("yes" if not triggers else "no"), ""])
    assessment = {"schema": "yao-bp4-tuning-stopping-v1", "stage": stage, "confidence": .9,
                  "stage_results_sha256": sha256(result_path.read_bytes()).hexdigest(),
                  "stage_plan_sha256": plan_sha, "codes": codes}
    prefix = "stopping_assessment" if stage == "validate" else f"{stage}_stopping_assessment"
    (ROOT / "results" / f"{prefix}.json").write_text(json.dumps(assessment, sort_keys=True, indent=2) + "\n")
    (ROOT / "results" / f"{prefix}.md").write_text("\n".join(lines))
    print({code: value["stop_in_tested_neighborhood"] for code, value in codes.items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=("validate", "followup", "joint_final", "a5_prior", "a5_low_prior", "a5_tiny_prior", "a5_final_neighborhood", "a5_d02_neighborhood", "b2_prior_confirm"), default="validate")
    main(parser.parse_args().stage)
