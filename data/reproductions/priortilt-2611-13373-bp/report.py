"""Publish only complete BP points that passed a fresh ledger audit."""
import csv
import io

import run


def checked_row(plan, index):
    job = plan["jobs"][index]
    folder = run.ROOT / "results" / job["id"]
    path = folder / "audit.json"
    if not path.exists():
        return None
    resolved = run.resolve_job(plan, index)
    audit = run.read_json(path)
    manifest_path = folder / "manifest.json"
    manifest = run.read_json(manifest_path)
    if (audit != run.read_json(folder / "complete.json") or manifest["job"] != resolved
            or audit["job"] != resolved or audit["resolved_policy"] != resolved["spec"]
            or audit["plan_sha256"] != run.sha(run.ROOT / "plan.json")
            or audit["manifest_sha256"] != run.sha(manifest_path)
            or audit["work_sha256"] != run.identity(run.read_json(folder / "parallel-work.json"))):
        raise ValueError(f"audit identity changed for {job['id']}")
    row = {k: job[k] for k in ("id", "mode", "code", "p", "cycles", "method")}
    row.update(resolved["spec"])
    row["selection_sha256"] = resolved["selection_sha256"]
    plan = run.effective_plan(plan, resolved)
    cycles = row["cycles"]
    xz = []
    for basis in run.BASES:
        summary = audit["bases"][basis]
        base = {k: v for k, v in summary.items() if k not in ("rate", "ci975", "stop_reason")}
        if summary != run.terminal(base, plan):
            raise ValueError("terminal summary changed")
        shots = summary["shots"]
        for name, digest in summary["chunks"].items():
            marker = folder / basis / name
            if run.sha(marker) != digest:
                raise ValueError("audited ledger marker changed")
            meta = run.read_json(marker)
            if run.sha(marker.with_suffix(".npz")) != meta["sha256"]:
                raise ValueError("audited ledger bytes changed")
            run.verify_noise_binding(plan, resolved, basis, meta["start"], meta)
        for k in ("shots", "errors", "nonconvergence", "stop_reason"):
            row[f"{basis}_{k}"] = summary[k]
        row[f"{basis}_mean_iterations"] = summary["iterations"] / shots
        row[f"{basis}_mean_directed_edge_updates"] = summary["directed_edge_updates"] / shots
        row[f"{basis}_mean_decode_ms"] = summary["decode_ns"] / shots / 1e6
        xz.append(summary)
    row["ler_per_cycle"] = sum(v["rate"] for v in xz) / cycles
    row["ci95_low"], row["ci95_high"] = (sum(v["ci975"][i] for v in xz) / cycles for i in (0, 1))
    row["audit_sha256"] = run.sha(path)
    return row


def atomic_text(path, content):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content)
    temp.replace(path)


def collect(plan):
    with run.lock(run.ROOT / "publish.lock", True):
        rows = [row for i in range(len(plan["jobs"])) if (row := checked_row(plan, i))]
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else
                                ["id", "mode", "code", "p", "cycles", "method", "ler_per_cycle", "ci95_low", "ci95_high"])
        writer.writeheader()
        writer.writerows(rows)
        atomic_text(run.ROOT / "comparison.csv", stream.getvalue())
        lines = ["# Canonical BP on the PriorTilt benchmarks", "",
                 f"{len(rows)}/{len(plan['jobs'])} decoder points completed fresh audits.", "",
                 "The comparison uses released XZ and XYZ evaluation circuits, 18,080 sweeps, "
                 "and 20 observable errors or 100 million shots per memory basis. The reported "
                 "LER per cycle is the sum of the X- and Z-memory rates divided by the cycle count.", "",
                 "| Mode | Code | p | Method | Damping / scaling / offset | X errors / shots | Z errors / shots | LER/cycle [95%] |",
                 "|---|---|---:|---|---|---:|---:|---:|"]
        for r in rows:
            lines.append(f"| {r['mode'].upper()} | {r['code']} | {r['p']} | {r['method']} | "
                         f"{r['damping']} / {r['alpha']} / {r['beta']} | {r['x_errors']}/{r['x_shots']} | "
                         f"{r['z_errors']}/{r['z_shots']} | {r['ler_per_cycle']:.5g} "
                         f"[{r['ci95_low']:.5g}, {r['ci95_high']:.5g}] |")
        lines += ["", "The CSV includes per-basis mean iterations, directed edge updates and instrumented decoder time.",
                  "The [XZ and XYZ reports](README.md) link the existing paper benchmarks."]
        atomic_text(run.ROOT / "RESULTS.md", "\n".join(lines) + "\n")
        print(f"Published {len(rows)}/{len(plan['jobs'])} audited BP points", flush=True)


if __name__ == "__main__":
    collect(run.load())
