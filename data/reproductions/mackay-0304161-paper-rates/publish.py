"""Publish the paper-rate evidence without mixing it into the old interval."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json

from run import ORIGINAL, PLAN, REPO, RESULTS, ROOT, load_plan, sha, write_json

# Reuse the established normalized-format adapter. Its `from run` binding is
# this campaign, and the adapter bytes remain frozen historical implementation.
spec = importlib.util.spec_from_file_location("_paper_rate_catalog_adapter", ORIGINAL / "publish.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
DATASET = "mackay-unicycle-paper-rates"


def extension(plan, receipt):
    if receipt["schema"] != "mackay-paper-rates-verification-v1" or receipt["plan_sha256"] != sha(PLAN):
        raise ValueError("verified paper-rate results do not match the frozen plan")
    data = adapter.extension(plan, {**receipt, "schema": "mackay-unicycle-verification-v1"})

    def rename(value):
        if isinstance(value, dict):
            return {key: rename(child) for key, child in value.items()}
        if isinstance(value, list):
            return [rename(child) for child in value]
        if isinstance(value, str) and value.startswith("mackay-unicycle-bp"):
            return value.replace("mackay-unicycle-bp", DATASET, 1)
        return value

    data = rename(data)
    # The original extension already registers this same paper identity.
    data["papers"] = []
    data["datasets"][0]["label"] = "MacKay BP at the published error rates"
    relative = ROOT.relative_to(REPO).as_posix()
    for asset in data["datasets"][0]["assets"]:
        if asset["path"].endswith("/source.json"):
            asset.update(path=f"{relative}/source_points.json", label="Source-plot error rates and coordinates")
        elif asset["path"].endswith("/codes.json"):
            asset["path"] = str((ORIGINAL / "codes.json").relative_to(REPO))
    by_key = {(r["code"], r["arm"], r["physical_p"]): r for r in receipt["points"]}
    for series in data["result_series"]:
        for point in series["points"]:
            row = by_key[(series["code_id"], series["source_decoder_id"], point["x"])]
            target = row["source_target"]
            point["source_value"] = None if target is None else target["total_error_approx"]
            point["metadata"].update(
                cohort_kind="paper_rate_validation", source_target=target,
                classical_block_errors=row["classical_block_errors"],
                classical_block_error_rate=row["classical_block_error_rate"],
                certified_branches_pruned=row["certified_branches_pruned"],
                classical_uncertainty="not inferred from quantum-failure stopping when stabilizer successes occur")
    data["datasets"][0]["points"] = [deepcopy(p) for s in data["result_series"] for p in s["points"]]
    return data


if __name__ == "__main__":
    plan = load_plan()
    receipt = json.loads((RESULTS / "verified.json").read_text())
    write_json(ROOT / "verified.json", receipt)
    write_json(ROOT / "catalog.json", extension(plan, receipt))
    print(f"Published {len(receipt['points'])}/{receipt['planned_points']} paper-rate points")
