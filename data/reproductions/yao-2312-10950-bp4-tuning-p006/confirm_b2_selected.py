"""Attach the independent B2 prior-reselection receipt to its decoder file."""

from __future__ import annotations

from hashlib import sha256
import json

from runner import ROOT, load_registry


def main() -> None:
    path = ROOT / "decoders/b2_tuned.json"
    registry, _, _ = load_registry(path)
    receipt_raw = (ROOT / "results/b2_reselection_assessment.json").read_bytes()
    receipt = json.loads(receipt_raw)
    result_raw = (ROOT / "results/b2_prior_confirm_results.json").read_bytes()
    if (registry["selected_candidate_id"] != receipt["retained_candidate_id"]
            or not receipt["stop_in_tested_prior_neighborhood"]
            or receipt["stage_results_sha256"] != sha256(result_raw).hexdigest()
            or "confirmation_stage" in registry):
        raise ValueError("B2 selected decoder and independent evidence mismatch")
    registry["confirmation_stage"] = "b2_prior_confirm"
    registry["confirmation_results_sha256"] = sha256(result_raw).hexdigest()
    registry["confirmation_reselection_sha256"] = sha256(receipt_raw).hexdigest()
    registry["confirmation_shots"] = receipt["retained_shots"]
    registry["confirmation_failures"] = receipt["retained_failures"]
    path.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n")
    load_registry(path)
    print(path)


if __name__ == "__main__":
    main()
