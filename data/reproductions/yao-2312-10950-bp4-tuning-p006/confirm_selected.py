"""Attach the final fresh-seed interaction audit to unchanged selected policies."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, load_registry


def main() -> None:
    plan_raw = (ROOT / "joint_final_plan.json").read_bytes()
    plan = json.loads(plan_raw)
    result_raw = (ROOT / "results/joint_final_results.json").read_bytes()
    result = json.loads(result_raw)
    assessment_raw = (ROOT / "results/joint_final_stopping_assessment.json").read_bytes()
    assessment = json.loads(assessment_raw)
    if (not result["complete"] or result["plan_sha256"] != sha256(plan_raw).hexdigest()
            or assessment["stage_results_sha256"] != sha256(result_raw).hexdigest()
            or assessment["stage_plan_sha256"] != sha256(plan_raw).hexdigest()):
        raise ValueError("final interaction evidence is incomplete or mismatched")
    for code in ("a5", "b2"):
        if not assessment["codes"][code]["stop_in_tested_neighborhood"]:
            raise ValueError(f"{code} did not meet the final-grid stopping rule")
        path = ROOT / "decoders" / f"{code}_tuned.json"
        registry, _, _ = load_registry(path)
        if (registry["selected_candidate_id"] != plan["incumbents"][code]
                or "confirmation_stage" in registry):
            raise ValueError(f"{code} selected decoder changed or already confirmed")
        row = next((row for row in result["rows"]
                    if row["code"] == code and row["candidate_id"] == registry["selected_candidate_id"]), None)
        if row is None:
            raise ValueError(f"{code} incumbent absent from final grid")
        registry["confirmation_stage"] = "joint_final"
        registry["confirmation_plan_sha256"] = sha256(plan_raw).hexdigest()
        registry["confirmation_results_sha256"] = sha256(result_raw).hexdigest()
        registry["confirmation_stopping_sha256"] = sha256(assessment_raw).hexdigest()
        registry["confirmation_shots"] = row["shots"]
        registry["confirmation_failures"] = row["failures"]
        path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
        load_registry(path)
        print(path)


if __name__ == "__main__":
    main()
