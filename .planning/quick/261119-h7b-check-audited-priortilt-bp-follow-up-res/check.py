"""Derive a status table from audited BP receipts and sample raw bindings."""
from collections import Counter
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BP = REPO / "data/reproductions/priortilt-2611-13373-bp"
sys.path.insert(0, str(BP))
import run

plan = run.load()
plan_digest = run.sha(BP / "plan.json")
rows, progress, selections = [], {}, {}
sampled = 0
for index, job in enumerate(plan["jobs"]):
    point = BP / "results" / job["id"]
    path = point / "audit.json"
    if not path.exists():
        status = next((p for p in (point / "complete.json", point / "progress.json") if p.exists()), None)
        if status is not None:
            progress[job["id"]] = {
                "file": status.name,
                "bases": {b: {k: stats[k] for k in ("shots", "errors", "rescaled_shots")}
                          for b, stats in run.read_json(status)["bases"].items()}}
        else:
            progress[job["id"]] = {"file": None}
        continue

    resolved = run.resolve_job(plan, index)
    manifest_path = point / "manifest.json"
    manifest = run.read_json(manifest_path)
    audit = run.read_json(path)
    assert audit == run.read_json(point / "complete.json")
    assert manifest["job"] == audit["job"] == resolved
    assert manifest["plan_sha256"] == audit["plan_sha256"] == plan_digest
    assert audit["manifest_sha256"] == run.sha(manifest_path)
    assert audit["resolved_policy"] == resolved["spec"] and audit["workers"] == 20
    work = run.read_json(point / "parallel-work.json")
    assert audit["work_sha256"] == run.identity(work)
    row = {k: job[k] for k in ("id", "mode", "code", "p", "cycles", "method")}
    row.update(resolved["spec"])
    row["audit_sha256"] = run.sha(path)
    row["selection_sha256"] = resolved["selection_sha256"]
    low, high, rate, shots, iterations, edges = 0., 0., 0., 0, 0, 0
    effective = run.effective_plan(plan, job)
    for basis, s in audit["bases"].items():
        n, k = s["shots"], s["errors"]
        assert k == 20 or n == 100_000_000
        assert 0 <= k <= 20 and 0 < n <= 100_000_000
        joint = s["joint_counts"]
        assert sum(joint) == n and joint[1] + joint[3] == k
        assert joint[2] + joint[3] == s["nonconvergence"]
        assert s["stop_reason"] == ("target_observable_errors" if k == 20 else "shot_cap")
        assert s["rescaled_shots"] <= min(s["llr_rescales"], n)
        ci_l = float(beta.ppf(.0125, k, n-k+1)) if k else 0.
        ci_h = float(beta.ppf(.9875, k if k == 20 else k+1, n-k)) if k < n else 1.
        assert math.isclose(k/n, s["rate"], rel_tol=1e-12)
        np.testing.assert_allclose(s["ci975"], [ci_l, ci_h], rtol=1e-12, atol=0)
        assert n <= s["iterations"] <= n * resolved["spec"]["iterations"]
        names = sorted(s["chunks"])
        for ix in sorted({0, len(names)//2, len(names)-1}):
            marker = point / basis / names[ix]
            assert run.sha(marker) == s["chunks"][names[ix]]
            meta = run.read_json(marker)
            assert run.sha(marker.with_suffix(".npz")) == meta["sha256"]
            run.verify_noise_binding(effective, resolved, basis, meta["start"], meta)
            sampled += 1
        for key in ("shots", "errors", "nonconvergence", "rescaled_shots", "llr_rescales", "stop_reason"):
            row[basis + "_" + key] = s[key]
        row[basis + "_mean_iterations"] = s["iterations"]/n
        row[basis + "_mean_directed_edge_updates"] = s["directed_edge_updates"]/n
        row[basis + "_mean_decode_ms"] = s["decode_ns"]/n/1e6
        rate += k/n
        low += ci_l
        high += ci_h
        shots += n
        iterations += s["iterations"]
        edges += s["directed_edge_updates"]
    row.update(ler_per_cycle=rate/job["cycles"], ci95_low=low/job["cycles"], ci95_high=high/job["cycles"],
               shot_weighted_mean_iterations=iterations/shots, shot_weighted_mean_directed_edge_updates=edges/shots)
    for key in ("shots", "errors", "iterations", "directed_edge_updates", "decode_ns", "nonconvergence"):
        assert sum(s[key] for s in audit["bases"].values()) == work["retained"][key]
        assert work["retained"][key] + work["speculative"][key] == work["computed"][key]
    rows.append(row)

for group in plan["training_points"]:
    path = run.selection_path(group)
    if not path.exists():
        folder = path.parent
        selections[group] = {"sealed_training_blocks": {
            directory.name: sum(1 for _ in directory.glob("*/*.json"))
            for directory in sorted(folder.glob("round-*")) if directory.is_dir()}}
        continue
    selection = run.read_json(path)
    assert selection["plan_sha256"] == plan_digest and selection["group"] == group
    assert selection["p"] == .003 and selection["iteration_limit"] == 18080
    rounds = selection["rounds"]
    for stage in rounds:
        for candidate in stage["ranked"]:
            assert len(candidate["chunks"]) > 0
            for key in ("errors", "iterations"):
                assert candidate[key] == sum(b[key] for b in candidate["bases"].values())
            assert all(b["shots"] == stage["shots_per_basis"] for b in candidate["bases"].values())
    ranked = rounds[-1]["ranked"]
    minimum = min(x["errors"] for x in ranked)
    winner = min((x for x in ranked if x["errors"] <= minimum+1),
                 key=lambda x: (x["iterations"], x["errors"], run.identity(x["controls"])))
    assert selection["controls"] == winner["controls"]
    selections[group] = {"controls": selection["controls"], "final_shots_per_basis": rounds[-1]["shots_per_basis"],
                         "final_scores": [{k: x[k] for k in ("controls", "errors", "iterations")} for x in ranked],
                         "receipt_sha256": run.sha(path)}

with (HERE / "audited-bp.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

prior = {}
parent = REPO / "data/reproductions/priortilt-2611-13373"
for row in csv.DictReader((parent / "comparison.csv").open()):
    if row["method"] == "priortilt":
        prior[row["code"], float(row["p"])] = float(row["ler_per_cycle"])

xyz = {}
study = REPO / "data/reproductions/priortilt-2611-13373-xyz"
for j in run.read_json(study / "plan.json")["jobs"]:
    folder = study / "results" / j["id"]
    receipt = next(p for p in (folder / "audit.json", folder / "complete.json", folder / "progress.json") if p.exists())
    a = run.read_json(receipt)
    if receipt.name == "audit.json":
        assert a == run.read_json(folder / "complete.json")
    xyz[j["method"]] = {"receipt": receipt.name,
                        "bases": {b: {k: s[k] for k in ("shots", "errors", "iterations", "directed_edge_updates")}
                                  for b, s in a["bases"].items()}}
    if receipt.name == "audit.json":
        xyz[j["method"]]["ler_per_cycle"] = sum(s["rate"] for s in a["bases"].values()) / j["cycles"]

source = {r["method"]: float(r["ler_per_cycle"])
          for r in csv.DictReader((study / "source-table4.csv").open())}
keyed = {(r["mode"], r["code"], r["p"], r["method"]): r for r in rows}
comparisons = []
for r in rows:
    if r["method"] != "bp":
        continue
    mode, code, p = r["mode"], r["code"], r["p"]
    other = keyed.get((mode, code, p, "tuned-bp"))
    pair = {"mode": mode, "code": code, "p": p, "bp_ler": r["ler_per_cycle"],
            "tuned_ler": other["ler_per_cycle"] if other else None,
            "bp_mean_iterations": r["shot_weighted_mean_iterations"],
            "tuned_mean_iterations": other["shot_weighted_mean_iterations"] if other else None,
            "local_xz_prior_tilt_ler": prior.get((code,p)) if mode == "xz" else None}
    if other:
        pair["tuned_over_bp_ler"] = other["ler_per_cycle"]/r["ler_per_cycle"]
        pair["tuned_over_bp_mean_iterations"] = other["shot_weighted_mean_iterations"]/r["shot_weighted_mean_iterations"]
        pair["pointwise_intervals_overlap"] = max(r["ci95_low"], other["ci95_low"]) <= min(r["ci95_high"], other["ci95_high"])
    comparisons.append(pair)

ids = "62119937,62119938,62119939,62119941,62119943,62119945,62119946,62102101,62102102"
slurm = subprocess.check_output(["squeue", "-r", "-h", "-j", ids, "-o", "%i|%j|%T|%C|%M|%R"], text=True)
(HERE / "scheduler.txt").write_text(slurm)
summary = {"utc": datetime.now(timezone.utc).isoformat(), "frozen_plan_sha256": plan_digest,
           "frozen_files": len(plan["implementation_sha256"]), "audited_rows": len(rows),
           "audit_count_by_mode_method": dict(Counter(r["mode"] + " " + r["method"] for r in rows)),
           "audited_shots": sum(r[b + "_shots"] for r in rows for b in run.BASES),
           "audited_errors": sum(r[b + "_errors"] for r in rows for b in run.BASES),
           "sampled_bound_chunks": sampled, "training": selections, "progress": progress,
           "xyz_paper_runs": xyz, "xyz_source_ler_per_cycle": source, "comparisons": comparisons,
           "scope": "Fresh receipt and aggregate reconciliation with first/middle/last bound chunks per basis. "
                    "Final worker audits cover all retained and speculative ledgers. Scheduled collector repeats full publication rehash."}
(HERE / "assessment.json").write_text(json.dumps(summary, indent=2) + "\n")
print("Verified", len(rows), "audited BP results,", sampled, "sampled chunks,",
      summary["audited_shots"], "shots and", summary["audited_errors"], "errors")
