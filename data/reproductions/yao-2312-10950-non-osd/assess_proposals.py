"""Verify fixed proposal-screen shot ledgers and select by failure ESS per shot."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from importance_assess import verified_importance_runs

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def assess(plan_path: Path) -> dict:
    plan_path = plan_path.resolve()
    plan = json.loads(plan_path.read_text())
    if plan["schema"] != "yao-importance-proposal-screen-v1":
        raise ValueError("unexpected proposal screen schema")
    if sha256((ROOT / "run_importance.py").read_bytes()).hexdigest() != plan["runner_sha256"]:
        raise ValueError("proposal screen runner drift")
    rows = []
    for job in plan["jobs"]:
        summary_path = REPO / job["output"] / "summary.json"
        key = (job["code"], job["method"], f'{job["p"]:.5f}')
        result = verified_importance_runs([summary_path])[key]
        if (result["shots"] != job["shots"] or result["proposals"] != [job["proposal_p"]]
                or result["analysis_stage"] != 0):
            raise ValueError(f"proposal screen plan/run mismatch: {summary_path}")
        rows.append({"code": job["code"], "method": job["method"], "p": job["p"],
                     "proposal_p": job["proposal_p"], "shots": result["shots"],
                     "raw_failures": result["raw_failures"], "rate": result["rate"],
                     "failure_ess": result["failure_ess"],
                     "failure_ess_per_shot": result["failure_ess"] / result["shots"],
                     "summary_path": str(summary_path.relative_to(REPO)),
                     "summary_sha256": sha256(summary_path.read_bytes()).hexdigest()})
    selected = sorted(rows, key=lambda row: (-row["failure_ess_per_shot"], row["proposal_p"]))[0]
    return {"schema": "yao-importance-proposal-screen-assessment-v1",
            "plan": str(plan_path.relative_to(REPO)),
            "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(),
            "selection_metric": plan["selection_metric"],
            "selected_proposal_p": selected["proposal_p"], "rows": rows,
            "screen_shots_excluded_from_final_estimate": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.plan)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"selected_proposal_p": result["selected_proposal_p"],
                      "rows": len(result["rows"])}))
