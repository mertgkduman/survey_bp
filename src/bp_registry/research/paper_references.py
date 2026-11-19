"""Extract figure-scoped reference markers from retained primary-source evidence."""
from __future__ import annotations

from collections import defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path


def add_paper_references(catalog: dict, root: Path) -> None:
    """Attach reference data to figures without changing any measured series."""
    figures = {figure["figure_id"]: figure for figure in catalog.get("paper_figures", [])}

    def add(figure_id, code, channel, matches, coordinates, path, kind, metric):
        points = sorted(
            ({"x": float(x), "y": float(y)} for x, y in coordinates),
            key=lambda point: point["x"],
        )
        if (not points or len({point["x"] for point in points}) != len(points)
                or any(not (0 <= point["x"] <= 1 and 0 < point["y"] <= 1) for point in points)):
            raise ValueError(f"invalid paper coordinates in {path} for {figure_id}/{code}")
        figure = figures[figure_id]
        figure.setdefault("reference_curves", []).append({
            "code_id": code,
            "channel_kind": channel,
            "matches": [{"dataset_id": dataset, "source_decoder_id": arm} for dataset, arm in matches],
            "source_path": path,
            "source_paper_id": figure.get("guest_paper_id", figure["paper_id"]),
            "source_kind": kind,
            "metric": metric,
            "points": points,
        })

    if "yao-fig-2" in figures:
        path = "data/reproductions/yao-2312-10950-non-osd/source_points.json"
        source = json.loads((root / path).read_text())
        for number, panel in source["figures"].items():
            figure_id = f"yao-fig-{number}"
            if figure_id not in figures:
                continue
            rules = {rule["dataset_id"]: set(rule["source_decoder_ids"])
                     for rule in figures[figure_id]["reproduction_rules"]}
            code = panel["code"]
            for arm, coordinates in panel["curves"].items():
                if arm not in rules.get("yao-non-osd-results", set()):
                    continue
                completed_arm = (
                    f"{arm}_r{1922 if code == 'c2' else 882}"
                    if arm in {"bpgd_t1", "bpgd_t10", "bpgd_t70", "bpgd_t100"} else arm
                )
                matches = [("yao-non-osd-results", arm)]
                if completed_arm in rules.get("yao-bpgd-completion", set()):
                    matches.insert(0, ("yao-bpgd-completion", completed_arm))
                add(figure_id, code, "depolarizing" if number in {"7", "8"} else "x_only",
                    matches, coordinates.items(), path, "published", "Block failure rate")

    if "roffe-fig-3" in figures:
        path = "data/reproductions/roffe-2005-07016-bp/source_points.json"
        source = json.loads((root / path).read_text())
        for size, rows in source["curves"].items():
            add("roffe-fig-3", f"toric{size}", "x_only",
                [("roffe-2020-figure3-canonical-bp", "binary_ms"),
                 ("roffe-damping-confirmation", "binary_ms_baseline")],
                ((row["p"], row["block_ler_approx"]) for row in rows),
                path, "digitized", "Block failure rate")

    if "mackay-fig-15" in figures:
        path = "data/reproductions/mackay-0304161-paper-rates/source_points.json"
        source = json.loads((root / path).read_text())
        add("mackay-fig-15", "unicycle274", "x_only", [("mackay-inferred-t100-baseline", "unicycle_sp")],
            ((row["p"], row["total_error_approx"]) for row in source["points"].values()),
            path, "digitized", "Classical block error rate")

    if "priortilt-figure-1" in figures:
        path = "data/reproductions/priortilt-2611-13373/source-figure1.csv"
        methods = {"PriorTilt_3phase": "priortilt", "RelayBP": "relay", "BeamSearch32": "beam"}
        by_curve = defaultdict(list)
        with (root / path).open(newline="") as handle:
            for row in csv.DictReader(handle):
                by_curve[row["code"], methods[row["method"]]].append((row["p"], row["ler_per_cycle"]))
        for (code, method), coordinates in by_curve.items():
            for figure_id in ("priortilt-figure-1", f"{method}-priortilt-figure-1"):
                if figure_id in figures:
                    add(figure_id, f"priortilt-{code.lower()}-memory-x", "embedded_circuit",
                        [("priortilt-figure-1-canonical", f"priortilt-paper-{method}")],
                        coordinates, path, "published", "Logical error rate per cycle")

    paths = {reference["source_path"] for figure in figures.values()
             for reference in figure.get("reference_curves", [])}
    for path in sorted(paths):
        catalog.setdefault("extension_sources", []).append({
            "path": path,
            "sha256": sha256((root / path).read_bytes()).hexdigest(),
        })
