"""Audit and compare all long-cap candidates pairwise on identical shots."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from itertools import combinations

from scipy.stats import beta

from analyze_fixed import paired_p
from analyze_screen import _task_events
from runner import ROOT, REPO, load_registry


def compare(stage: str) -> dict[str, object]:
    if stage not in {"tail_a5", "tail_b2", "sweet_b2", "a5_d02_neighborhood"}:
        raise ValueError("unknown cap-tail stage")
    result_raw = (ROOT / "results" / f"{stage}_results.json").read_bytes()
    result = json.loads(result_raw)
    if not result["complete"] or result["stage"] != stage:
        raise ValueError("complete audited cap-tail results required")
    plan_raw = (ROOT / f"{stage}_plan.json").read_bytes()
    plan = json.loads(plan_raw)
    plan_sha = sha256(plan_raw).hexdigest()
    if result["plan_sha256"] != plan_sha:
        raise ValueError("result and frozen plan differ")
    _, candidates, registry_sha = load_registry(REPO / plan["candidate_registry"])
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("registry and frozen plan differ")
    rate_rows = {row["candidate_id"]: row for row in result["rows"]}
    outcomes = {}
    for task in plan["tasks"]:
        _, failures, _ = _task_events(task, plan, plan_sha)
        outcomes[task["candidate_id"]] = failures
    if len(plan["points"]) != 1:
        raise ValueError("pairwise comparison requires one code")
    code = next(iter(plan["points"]))
    ids = plan["points"][code]["candidate_ids"]
    rows = []
    for left, right in combinations(ids, 2):
        old, new = outcomes[left], outcomes[right]
        rescues = sum(o and not n for o, n in zip(old, new, strict=True))
        losses = sum(n and not o for o, n in zip(old, new, strict=True))
        left_spec, right_spec = candidates[left], candidates[right]
        only_cap_increases = (left_spec["kernel"] == right_spec["kernel"] == "profile_v2"
                              and all(left_spec[key] == right_spec[key]
                                      for key in ("p0", "damping", "check_cap", "product_epsilon"))
                              and right_spec["max_iterations"] > left_spec["max_iterations"])
        rescue_upper90 = (1.0 if rescues == len(old) else
                          float(beta.ppf(.9, rescues + 1, len(old) - rescues)))
        left_margin = (rate_rows[left]["ler"] - rate_rows[left]["ci90_lower"])
        cap_saturated = (rescue_upper90 < left_margin
                         and rate_rows[right]["ler"] >= rate_rows[left]["ci90_lower"]
                         if only_cap_increases else None)
        rows.append({"left": left, "right": right, "shots": len(old),
                     "left_failures": sum(old), "right_failures": sum(new),
                     "rescues_left_to_right": rescues, "losses_left_to_right": losses,
                     "rate_difference_right_minus_left": (sum(new) - sum(old)) / len(old),
                     "p_right_better": paired_p(rescues, losses),
                     "p_left_better": paired_p(losses, rescues),
                     "only_cap_increases": only_cap_increases,
                     "rescue_rate_upper90": rescue_upper90,
                     "left_rate_to_lower_ci90_margin": left_margin,
                     "cap_saturated90": cap_saturated})
    output = {"schema": "yao-bp4-tail-pairwise-v1", "stage": stage, "code": code,
              "plan_sha256": plan_sha, "results_sha256": sha256(result_raw).hexdigest(),
              "rows": rows}
    out = ROOT / "results"
    (out / f"{stage}_pairwise.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    with (out / f"{stage}_pairwise.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = [f"# {code.upper()} long-cap paired comparisons", "",
             "Positive rescues mean the right candidate corrected a failure of the left.",
             "P-values are one-sided exact McNemar tests and unadjusted for multiple comparisons.",
             "For cap-only increases, saturation requires the exact one-sided 90% upper bound",
             "on rescue rate to fit inside the left candidate's exact two-sided 90% LER interval.", "",
             "| Left | Right | Failures left/right | Rescues/losses | p(right better) | Rescue upper 90% | Cap saturated? |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['left']} | {row['right']} | "
                     f"{row['left_failures']}/{row['right_failures']} | "
                     f"{row['rescues_left_to_right']}/{row['losses_left_to_right']} | "
                     f"{row['p_right_better']:.4g} | {row['rescue_rate_upper90']:.5g} | "
                     f"{('yes' if row['cap_saturated90'] else 'no') if row['only_cap_increases'] else 'N/A'} |")
    (out / f"{stage}_pairwise.md").write_text("\n".join(lines) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("tail_a5", "tail_b2", "sweet_b2", "a5_d02_neighborhood"))
    args = parser.parse_args()
    result = compare(args.stage)
    print(f"audited {len(result['rows'])} paired comparisons for {result['code'].upper()}")
