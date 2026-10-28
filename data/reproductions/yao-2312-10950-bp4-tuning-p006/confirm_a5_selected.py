"""Attach the audited finite-neighborhood decision to the A5 decoder file."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, load_registry


def main() -> None:
    path = ROOT / "decoders/a5_tuned.json"
    registry, _, _ = load_registry(path)
    assessment_raw = (ROOT / "results/a5_final_selection_assessment.json").read_bytes()
    assessment = json.loads(assessment_raw)
    if (registry["selected_candidate_id"] != assessment["selection"]
            or registry["selection_stage"] != "a5_d02_neighborhood"
            or registry["selection_stage_results_sha256"] != assessment["results_sha256"]
            or not assessment["stop_in_tested_neighborhood_with_cap_rule"]
            or "selection_assessment_sha256" in registry):
        raise ValueError("A5 selected decoder and final assessment mismatch")
    registry["selection_assessment_sha256"] = sha256(assessment_raw).hexdigest()
    registry["selection_shots"] = assessment["shots"]
    registry["selection_failures"] = assessment["failures"]
    path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    load_registry(path)
    print(path)


if __name__ == "__main__":
    main()
