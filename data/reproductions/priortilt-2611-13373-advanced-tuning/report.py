"""Publish audited unfiltered confirmation runs and selected controls."""
import csv
import io

import run


def result(plan, index):
    job = plan["jobs"][index]
    folder = run.ROOT / "results" / job["id"]
    path = folder / "audit.json"
    if not path.exists():
        return None
    resolved = run.resolve_job(plan, index)
    audit = run.read_json(path)
    manifest = folder / "manifest.json"
    if (audit != run.read_json(folder/"complete.json") or audit["job"] != resolved
            or audit["plan_sha256"] != run.sha(run.ROOT/"plan.json") or audit["manifest_sha256"] != run.sha(manifest)
            or audit["work_sha256"] != run.identity(run.read_json(folder/"parallel-work.json"))):
        raise ValueError("confirmation evidence identity changed")
    row = {k: job[k] for k in ("id", "mode", "code", "p", "method", "cycles")}
    row.update(resolved["controls"])
    row["selection_sha256"] = resolved["selection_sha256"]
    effective = run.effective_plan(plan, job)
    for b, summary in audit["bases"].items():
        aggregate = {k: v for k, v in summary.items() if k not in ("rate", "ci975", "stop_reason")}
        if summary != run.terminal(aggregate, effective):
            raise ValueError("confirmation stopping summary changed")
        for chunk, digest in summary["chunks"].items():
            marker = folder / b / chunk
            meta = run.read_json(marker)
            if run.sha(marker) != digest or run.sha(marker.with_suffix(".npz")) != meta["sha256"]:
                raise ValueError("audited confirmation chunk changed")
            run.verify_noise_binding(effective, job, b, meta["start"], meta)
        n = summary["shots"]
        for key in ("shots", "errors", "nonconvergence", "guarded_shots", "guarded_messages"):
            row[f"{b}_{key}"] = summary[key]
        row[f"{b}_mean_iterations"] = summary["iterations"]/n
        row[f"{b}_mean_directed_edge_updates"] = summary["directed_edge_updates"]/n
        row[f"{b}_mean_decode_ms"] = summary["decode_ns"]/n/1e6
    row["ler_per_cycle"] = sum(v["rate"] for v in audit["bases"].values())/job["cycles"]
    for i, label in enumerate(("low","high")):
        row[f"ci95_{label}"] = sum(v["ci975"][i] for v in audit["bases"].values())/job["cycles"]
    row["audit_sha256"] = run.sha(path)
    return row


def atomic(path, string):
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(string)
    tmp.replace(path)


def collect(plan):
    with run.lock(run.ROOT/"publish.lock", True):
        rows = [r for i in range(len(plan["jobs"])) if (r := result(plan, i))]
        stream = io.StringIO()
        out = csv.DictWriter(stream, list(rows[0]) if rows else ["id","mode","code","p","method","ler_per_cycle"])
        out.writeheader()
        out.writerows(rows)
        atomic(run.ROOT/"comparison.csv", stream.getvalue())
        text = ["# Tuned advanced BP confirmation", "", f"{len(rows)}/{len(plan['jobs'])} confirmation points audited.",
                "", "The rows use unfiltered memory samples and the parent decoder budgets.",
                "", "| Mode | Code | p | Method | Damping / scaling / offset | X errors / shots | Z errors / shots | LER/cycle [95%] |",
                "|---|---|---:|---|---|---:|---:|---:|"]
        for r in rows:
            text.append(f"| {r['mode'].upper()} | {r['code']} | {r['p']} | {r['method']} | "
                        f"{r['damping']} / {r['alpha']} / {r['beta']} | {r['x_errors']}/{r['x_shots']} | "
                        f"{r['z_errors']}/{r['z_shots']} | {r['ler_per_cycle']:.5g} "
                        f"[{r['ci95_low']:.5g}, {r['ci95_high']:.5g}] |")
        text.extend(["", "The [CSV](comparison.csv) includes per-basis mean sweeps, directed edge updates and decoder time."])
        atomic(run.ROOT/"RESULTS.md", "\n".join(text)+"\n")
        print(f"Published {len(rows)}/{len(plan['jobs'])} audited confirmations")


if __name__ == "__main__":
    collect(run.load())
