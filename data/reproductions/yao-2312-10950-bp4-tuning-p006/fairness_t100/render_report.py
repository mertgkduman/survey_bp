"""Build the source-backed BP4 fairness comparison report."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))

from runner import REPO, load_registry  # noqa: E402


FAIR = Path(__file__).resolve().parent


def main() -> None:
    plan_raw = (FAIR / "evaluation_plan.json").read_bytes()
    result = json.loads((FAIR / "evaluation_results.json").read_text())
    plan = json.loads(plan_raw)
    if not result["complete"] or result["plan_sha256"] != sha256(plan_raw).hexdigest():
        raise ValueError("complete audited paired evaluation required")
    _, candidates, registry_sha = load_registry(REPO / plan["candidate_registry"])
    if registry_sha != plan["candidate_registry_sha256"]:
        raise ValueError("candidate registry differs from frozen evaluation")
    rows = {(r["code"], r["candidate_id"]): r for r in result["rows"]}
    comparisons = {(c["code"], c["left"], c["right"]): c for c in result["comparisons"]}
    lines = ["# BP4 fairness comparison at physical p=0.06", "",
             "The previously quoted approximately 7.5–7.7× tuned-versus-untuned ratios",
             "combined parameter and iteration-cap changes on independent shot sets; they",
             "were not equal-budget comparisons. This fresh fixed-shot evaluation makes two",
             "paired comparisons on each",
             "code: **equal cap T=100**, and **approximately equal mean iterations**.",
             "Each code has 100,000 shared physical errors across its four arms. Exact and",
             "stabilizer-equivalent corrections count as successes; Type I syndrome mismatch",
             "and Type II logical failure count as block failures.", "",
             "The kernel is compiled canonical BP4 float64 v2 flooding sum-product in every",
             "arm. Untuned uses decoder prior p0=0.06, outgoing V2C damping d=0, no check cap,",
             "and check-product epsilon 1e-10. The tuned prior/damping were selected in the",
             "preceding study; only the cap is truncated to 100 in the equal-cap arm.", ""]
    for code in ("a5", "b2"):
        cap = plan["work_caps"][code]
        names = [("vanilla_t100", "Untuned, T=100"),
                 (f"tuned_t100_{code}", "Selected parameters, T=100"),
                 (f"vanilla_work_{code}", f"Untuned, T={cap:,}"),
                 (f"tuned_selected_{code}", "Selected parameters and cap")]
        lines.extend([f"## {code.upper()}", "",
                      "| Arm | p0 | d | T | Type I / II | Failures / N | LER (exact 90% CI) | Mean iterations | Mean ms/decode |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for name, label in names:
            row = rows[(code, name)]
            spec = candidates[name]
            lines.append(f"| {label} | {spec['p0']:g} | {spec['damping']:g} | "
                         f"{spec['max_iterations']:,} | {row['type_i']} / {row['type_ii']} | "
                         f"{row['failures']:,} / {row['shots']:,} | "
                         f"{row['ler']:.6g} [{row['ci90_lower']:.6g}, {row['ci90_upper']:.6g}] | "
                         f"{row['mean_iterations']:.3f} | {row['mean_decode_ms']:.3f} |")
        lines.extend(["", "| Paired comparison | Untuned/tuned failures | Rate ratio | Rescues/losses | p(tuned better) | Two-sided p |",
                      "|---|---:|---:|---:|---:|---:|"])
        for left, right, label in (("vanilla_t100", f"tuned_t100_{code}", "Equal T=100"),
                                   (f"vanilla_work_{code}", f"tuned_selected_{code}",
                                    "Pilot-calibrated mean work")):
            l, r = rows[(code, left)], rows[(code, right)]
            pair = comparisons[(code, left, right)]
            ratio = l["ler"] / r["ler"] if r["ler"] else float("inf")
            lines.append(f"| {label} | {l['failures']}/{r['failures']} | "
                         f"{ratio:.3g}× | {pair['rescues']}/{pair['losses']} | "
                         f"{pair['paired_improvement_p']:.3g} | "
                         f"{pair['paired_two_sided_p']:.3g} |")
        work_old = rows[(code, f"vanilla_work_{code}")]["mean_iterations"]
        work_new = rows[(code, f"tuned_selected_{code}")]["mean_iterations"]
        mismatch = (work_old - work_new) / work_new
        pilot = plan["pilot_work_selection"][code]
        lines.extend(["", f"The work-control cap was frozen at T={cap:,} from a separate 20,000-shot",
                      f"pilot. Its pilot mean was {pilot['vanilla_mean_iterations_at_cap']:.3f}",
                      f"versus the selected policy's earlier 100,000-shot target "
                      f"{pilot['tuned_selected_100k_mean_iterations']:.3f}. On the fresh",
                      f"evaluation, untuned averaged {work_old:.3f} and tuned averaged",
                      f"{work_new:.3f} iterations ({mismatch:+.1%} untuned relative to tuned).", ""])
        if code == "b2":
            pair = comparisons[(code, f"vanilla_work_{code}", f"tuned_selected_{code}")]
            lines.extend(["At approximately equal mean work, the B2 point estimate favors",
                          "untuned BP4. The two-sided paired difference is unresolved at 90% "
                          f"confidence (exact p={pair['paired_two_sided_p']:.3g}). "
                          f"A one-sided test in the observed untuned direction gives "
                          f"p={pair['paired_reverse_p']:.3g}; that direction was not "
                          "prespecified for this comparison.", ""])
    lines.extend(["## Interpretation and provenance", "",
                  "Equal T=100 controls the iteration cap; measured mean work can still differ",
                  "because the policies converge on different shots. The work control uses",
                  "mean completed iterations as the common unit on the same Tanner graph.",
                  "Wall time is listed separately and varies across HPC nodes; damping can",
                  "also change per-iteration arithmetic. The pilot chose caps without using",
                  "evaluation outcomes, and the tuning study chose priors/damping before this",
                  "fresh evaluation seed. These settings were optimized at longer caps, so",
                  "the T=100 arm is a cap-truncation control, not a new T=100 optimization.", "",
                  "All per-shot event ledgers, manifests, counts, source/policy hashes, and",
                  "sample-stream pairing passed [`analyze.py`](analyze.py). The fixed plans",
                  "and machine-readable results are in this folder. Raw ledgers remain on",
                  "the HPC filesystem and are excluded from Git; manifests and summaries",
                  "retain their SHA-256 digests. The [interval plot](comparison.pdf) shows",
                  "the four arms on each code.", ""])
    (FAIR / "REPORT.md").write_text("\n".join(lines))
    print(FAIR / "REPORT.md")


if __name__ == "__main__":
    main()
