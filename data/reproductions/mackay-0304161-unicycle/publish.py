"""Publish an audited snapshot through the existing normalized catalog format."""

from __future__ import annotations

from collections import defaultdict
import json

from run import PLAN, REPO, RESULTS, ROOT, load_plan, sha, write_json


def extension(plan: dict, receipt: dict) -> dict:
    if receipt["schema"] != "mackay-unicycle-verification-v1" or receipt["plan_sha256"] != sha(PLAN):
        raise ValueError("verified results do not match frozen campaign")
    dataset = "mackay-unicycle-bp"
    paper = "mackay-0304161-v3"
    relative = ROOT.relative_to(REPO).as_posix()
    labels = {"binary_sp": "Ordinary binary BP, SP, X-only",
              "unicycle_sp": "Unicycle two-hypothesis BP, SP, X-only",
              "qbp": "Q-BP, SP, depolarizing"}
    grouped = defaultdict(list)
    for row in receipt["points"]:
        n = row["shots"]
        grouped[(row["code"], row["arm"])].append({
            "x": row["physical_p"], "y": row["rate"], "n": n, "failures": row["failures"],
            "ci_low": row["ci95_low"], "ci_high": row["ci95_high"],
            "status": "complete" if row["failures"] else "upper_bound",
            "mean_work": row["iterations"] / n, "work_unit": "iterations",
            "mean_iterations": row["iterations"] / n,
            "mean_directed_edge_updates": row["directed_edge_updates"] / n,
            "iteration_unit": "branch sweeps" if row["arm"] == "unicycle_sp" else "sweeps",
            "mean_seconds": row["decode_ns"] / n / 1e9,
            "type_i": row["counts"]["type_i"], "type_ii": row["counts"]["type_ii"], "source_value": None,
            "metadata": {"matched_x_rate": row["matched_x_rate"],
                         "channel": plan["arms"][row["arm"]]["noise_model"],
                         "stop_reason": row["stop_reason"], "target_failures": 20, "max_shots": 100_000_000,
                         "sampling_method": "iid_failure_target_or_shot_cap", "seed": plan["seed"],
                         "uncertainty_method": "exact_negative_binomial_interval" if row["stop_reason"] == "target_block_failures"
                                               else "exact_binomial_interval_at_shot_cap",
                         "denominator_definition": "all retained iid shots; syndrome mismatch or either nontrivial logical residual",
                         "ledger_sha256": row["ledger_sha256"], "summary_sha256": row["summary_sha256"],
                         "source_evidence_path": f'{relative}/results/{row["id"]}/summary.json'},
        })
    series, decoders = [], []
    for (code, arm), points in sorted(grouped.items()):
        decoder_id = f"{dataset}:{code}:{arm}"
        label = labels[arm]
        series.append({"series_id": decoder_id, "dataset_id": dataset, "code_id": code,
                       "decoder_id": decoder_id, "source_decoder_id": arm, "label": label,
                       "channel_kind": plan["arms"][arm]["noise_model"],
                       "points": sorted(points, key=lambda p: p["x"])})
        decoders.append({"decoder_id": decoder_id, "label": label, "evidence_status": plan["evidence_status"],
                         "asset": {"path": f"{relative}/plan.json", "label": "Frozen campaign", "kind": "decoder_source"},
                         "configuration": {"settings_status": "exact_campaign_arm", "source_path": f"{relative}/plan.json",
                                           "source_arm_id": arm, "effective_configuration": plan["arms"][arm]}})
    return {"schema": "research-catalog-extension-v1",
            "papers": [{"paper_id": paper, "title": "Sparse Graph Codes for Quantum Error-Correction",
                        "identity": "quant-ph/0304161v3; IEEE TIT 2004", "kind": "paper",
                        "source_url": plan["paper"], "evidence_path": f"{relative}/source.json",
                        "registered_scope": "Construction U controlled BP campaign; not a paper-curve reproduction"}],
            "datasets": [{"dataset_id": dataset, "label": "MacKay unicycle BP and matched-marginal Q-BP",
                          "paper_id": paper, "source_path": f"{relative}/verified.json",
                          "evidence_status": plan["evidence_status"], "caveat": plan["claim_limit"],
                          "points": [p for s in series for p in s["points"]],
                          "assets": [{"path": f"{relative}/{name}", "kind": "json", "label": label}
                                     for name, label in (("plan.json", "Frozen experiment settings"),
                                                         ("verified.json", "Audited terminal results"),
                                                         ("source.json", "Source qualification"),
                                                         ("codes.json", "Code identities"))]}],
            "decoders": decoders, "result_series": series,
            "experiments": [{"experiment_id": dataset, "dataset_id": dataset, "dataset_ids": [dataset],
                             "paper_ids": [paper], "code_ids": sorted({s["code_id"] for s in series}),
                             "decoder_ids": [d["decoder_id"] for d in decoders],
                             "description": plan["claim_limit"], "evidence_status": plan["evidence_status"],
                             "reproduction_recipe": {"kind": "source_command", "study_path": f"{relative}/plan.json",
                                                     "decoder_path": f"{relative}/plan.json",
                                                     "commands": [f"PYTHONPATH=src .venv/bin/python {relative}/run.py --collect"],
                                                     "original_instruction_path": f"{relative}/README.md",
                                                     "budget_note": "Collection audits existing ledgers; point runs use frozen indices."}}]}


if __name__ == "__main__":
    plan = load_plan()
    receipt = json.loads((RESULTS / "verified.json").read_text())
    write_json(ROOT / "verified.json", receipt)
    write_json(ROOT / "catalog.json", extension(plan, receipt))
    print(f"Published {len(receipt['points'])}/{receipt['planned_points']} audited terminal points")
