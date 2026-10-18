#!/usr/bin/env python3
"""Extract non-authorizing Figure 2 vector and pinned author-result evidence.

Requires PyMuPDF. The PDF and author checkout are external inputs pinned by
content and commit; no decoder or production campaign is run here.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pymupdf


PDF_SHA256 = "0eec129dde3026f8225ec7d5f2884dbefe37566c9f71d105cae0195e4e4abca5"
AUTHOR_COMMIT = "816772071486615dfc7d71d1e15df597edc58a26"
REVIEW_DIGEST = "a5b9c6eb0bbe8a07743f5be093cc937c50759a07d5f60f8cebc3be557f4b49b5"
CURVES = {
    "bp4_baseline": (62, "BP4"),
    "bp4_asced_k16_delta2_l4": (66, "BP4_aSCED16_delta2"),
    "obp4_baseline": (63, "OBP4"),
    "obp4_asced_k16_delta2_l4": (68, "OBP4_aSCED16_delta2"),
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _vertices(drawing: dict) -> list[tuple[float, float]]:
    lines = [item for item in drawing["items"] if item[0] == "l"]
    if not lines:
        raise ValueError("selected drawing is not a vector path")
    return [(item[1].x, item[1].y) for item in lines] + [(lines[-1][2].x, lines[-1][2].y)]


def _interpolate(vertices: list[tuple[float, float]], x: float) -> tuple[float, bool]:
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:], strict=False):
        if x0 - 1e-5 <= x <= x1 + 1e-5:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0), abs(x - x0) > 1e-4 and abs(x - x1) > 1e-4
    raise ValueError(f"PDF x={x} lies outside selected vector path")


def build(pdf: Path, author_repo: Path) -> dict:
    if file_sha256(pdf) != PDF_SHA256:
        raise ValueError("primary PDF digest drifted")
    commit = subprocess.check_output(["git", "-C", str(author_repo), "rev-parse", "HEAD"], text=True).strip()
    if commit != AUTHOR_COMMIT:
        raise ValueError("author checkout is not pinned at the reviewed commit")
    page = pymupdf.open(pdf)[3]
    drawings = {drawing["seqno"]: drawing for drawing in page.get_drawings()}
    axis_x0, axis_x1 = 343.6555480957031, 539.762451171875
    axis_y0, axis_y5 = 64.239990234375, 217.8364715576172
    decade = (axis_y5 - axis_y0) / 5.0
    axis = {
        "pdf_page_one_based": 4,
        "pdf_coordinate_unit": "point",
        "x_anchors": [{"pdf_x": axis_x0, "p": 0.03}, {"pdf_x": axis_x1, "p": 0.10}],
        "y_anchors": [{"pdf_y": axis_y0, "ler": 1.0}, {"pdf_y": axis_y5, "ler": 1e-5}],
        "x_transform": "linear",
        "y_transform": "log10; log10(LER)=-(pdf_y-y0)/((y5-y0)/5)",
        "vector_centerline_bracket_pdf_points": 1.0,
        "bracket_scope": "conservative visual/vector reading only; excludes Monte Carlo uncertainty and curve identity error",
    }
    output: dict = {
        "schema": "phase11_asced_figure2_evidence_v1",
        "execution_authorized": False,
        "scientific_review_state": "supplemental_unreviewed",
        "review_candidate_sha256": REVIEW_DIGEST,
        "primary_pdf": {"url": "https://arxiv.org/pdf/2605.06547v2", "sha256": PDF_SHA256},
        "author_results": {"repository": "https://github.com/kit-cel/quantum_asced", "commit": AUTHOR_COMMIT},
        "method": {"extractor": "PyMuPDF get_drawings vector paths; linear interpolation in PDF space; axis transform", "pymupdf_version": pymupdf.VersionBind, "axis": axis},
        "curves": [],
        "blockers": [
            "author repository result files differ from Figure 2 for the ordinary BP4 baseline and some overcomplete points",
            "author repository meta target_errors differ from the paper's common 400-error statement for ordinary BP4 and BP4-aSCED",
            "author repository trials exceed the stated 1000000 max_trials for some low-p points",
            "PDF figure does not print per-point denominators; author result files cannot be substituted without review of the discrepancies",
            "source-curve statistical intervals, agreement tolerance, and reviewer signoff are not established by this extraction",
        ],
    }
    for curve_id, (seqno, folder) in CURVES.items():
        drawing = drawings[seqno]
        vertices = _vertices(drawing)
        result_dir = author_repo / "Results" / "GB_46_2" / folder
        ler_file, stats_file, meta_file = (result_dir / name for name in ("LER.json", "stats.json", "meta.txt"))
        ler, stats, meta = json.loads(ler_file.read_text()), json.loads(stats_file.read_text()), meta_file.read_text()
        settings = {line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip() for line in meta.splitlines() if ":" in line}
        rows = []
        for number in range(3, 11):
            p = number / 100
            key = f"{p:g}"
            pdf_x = axis_x0 + (p - .03) / .07 * (axis_x1 - axis_x0)
            pdf_y, interpolated = _interpolate(vertices, pdf_x)
            ordinate = lambda y: 10 ** (-(y - axis_y0) / decade)
            plotted = ordinate(pdf_y)
            lower, upper = ordinate(pdf_y + 1), ordinate(pdf_y - 1)
            count, trials = int(stats["logical_errors"][key]), int(stats["trials"][key])
            raw = float(ler[key])
            if abs(count / trials - raw) > 1e-12:
                raise ValueError(f"author LER/count mismatch: {folder} p={key}")
            rows.append({
                "p": p, "pdf_x": pdf_x, "pdf_y": pdf_y,
                "pdf_path_interpolated_at_p": interpolated,
                "plotted_ler": plotted,
                "plotted_ler_reading_interval": [lower, upper],
                "author_ler": raw,
                "author_logical_errors": count,
                "author_trials": trials,
                "author_over_stated_trial_cap": trials > int(settings["max_trials"]),
                "author_to_plotted_ratio": raw / plotted,
                "author_value_inside_plotted_reading_interval": lower <= raw <= upper,
            })
        output["curves"].append({
            "curve_id": curve_id, "pdf_drawing_seqno": seqno,
            "pdf_vector_vertices": [[x, y] for x, y in vertices],
            "author_folder": f"Results/GB_46_2/{folder}",
            "author_file_sha256": {name: file_sha256(result_dir / name) for name in ("LER.json", "stats.json", "meta.txt")},
            "author_meta": {key: settings.get(key) for key in ("target_errors", "max_trials", "max_iterations", "ensemble_size")},
            "points": rows,
        })
    output["evidence_sha256"] = sha256(canonical_bytes(output)).hexdigest()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--author-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.pdf, args.author_repo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"evidence_sha256": result["evidence_sha256"], "curves": len(result["curves"]), "points": sum(len(c["points"]) for c in result["curves"])}))


if __name__ == "__main__":
    main()
