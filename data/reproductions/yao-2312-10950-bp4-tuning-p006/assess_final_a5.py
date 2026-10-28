"""Apply the predeclared practical cap rule to the final A5 neighborhood."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT


def main() -> None:
    stage = "a5_d02_neighborhood"
    plan_raw = (ROOT / f"{stage}_plan.json").read_bytes()
    result_raw = (ROOT / "results" / f"{stage}_results.json").read_bytes()
    stop_raw = (ROOT / "results" / f"{stage}_stopping_assessment.json").read_bytes()
    pair_raw = (ROOT / "results" / f"{stage}_pairwise.json").read_bytes()
    plan, result, stop, pair = map(json.loads, (plan_raw, result_raw, stop_raw, pair_raw))
    incumbent = "sp_f64_v2_d02_p0005_t10000"
    cap = "sp_f64_v2_d02_p0005_t20000"
    cap_row = next((row for row in pair["rows"]
                    if row["left"] == incumbent and row["right"] == cap), None)
    if (not result["complete"] or result["plan_sha256"] != sha256(plan_raw).hexdigest()
            or stop["stage_results_sha256"] != sha256(result_raw).hexdigest()
            or pair["results_sha256"] != sha256(result_raw).hexdigest()
            or stop["codes"]["a5"]["incumbent_id"] != incumbent
            or stop["codes"]["a5"]["continued_tuning_triggers"] != [cap]
            or cap_row is None or cap_row["cap_saturated90"] is not True):
        raise ValueError("final A5 evidence does not satisfy the practical cap rule")
    row = next(r for r in result["rows"] if r["candidate_id"] == incumbent)
    assessment = {"schema": "yao-bp4-tuning-a5-final-v1",
                  "selection": incumbent,
                  "plan_sha256": sha256(plan_raw).hexdigest(),
                  "results_sha256": sha256(result_raw).hexdigest(),
                  "stopping_assessment_sha256": sha256(stop_raw).hexdigest(),
                  "pairwise_sha256": sha256(pair_raw).hexdigest(),
                  "failures": row["failures"], "shots": row["shots"],
                  "ler": row["ler"],
                  "ci90": [row["ci90_lower"], row["ci90_upper"]],
                  "mean_iterations": row["mean_iterations"],
                  "noncap_neighbor_triggers": [],
                  "cap_increase": {"from": incumbent, "to": cap,
                                   "rescues": cap_row["rescues_left_to_right"],
                                   "losses": cap_row["losses_left_to_right"],
                                   "one_sided_rescue_upper90": cap_row["rescue_rate_upper90"],
                                   "incumbent_rate_to_lower_ci90_margin":
                                   cap_row["left_rate_to_lower_ci90_margin"],
                                   "practically_saturated90": True},
                  "stop_in_tested_neighborhood_with_cap_rule": True}
    out = ROOT / "results/a5_final_selection_assessment"
    out.with_suffix(".json").write_text(json.dumps(assessment, sort_keys=True, indent=2) + "\n")
    out.with_suffix(".md").write_text(
        "# A5 final tested-neighborhood decision\n\n"
        f"Select `{incumbent}`: {row['failures']}/{row['shots']} = {row['ler']:.6g}; "
        f"exact 90% CI [{row['ci90_lower']:.6g}, {row['ci90_upper']:.6g}].\n\n"
        "No tested prior or damping neighbor triggered further tuning. "
        f"T=20,000 rescued {cap_row['rescues_left_to_right']}/{row['shots']} "
        f"with zero losses; its exact one-sided 90% rescue upper bound "
        f"{cap_row['rescue_rate_upper90']:.6g} is below the incumbent "
        f"LER-to-lower-CI margin {cap_row['left_rate_to_lower_ci90_margin']:.6g}. "
        "The T=20,000 point also stays within the incumbent interval. "
        "The finite neighborhood meets the predeclared practical cap rule; "
        "this is not a global optimum claim.\n")
    print(True)


if __name__ == "__main__":
    main()
