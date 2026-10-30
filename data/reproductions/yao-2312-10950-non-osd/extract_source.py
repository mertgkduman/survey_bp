"""Extract the paper's plotted values directly from its pinned arXiv TeX source."""

from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import tarfile
from urllib.request import urlopen

URL = "https://export.arxiv.org/src/2312.10950v2"
ARCHIVE_SHA256 = "8ddade4c50c9b12853e5431c53f4906fd29913bbf3be306422bafd984a05d654"
TEX_SHA256 = "019ef045f0f1c4826267cdb3bd6880b3a9d8f9e64f4d7e4ab8defb8209f8add2"
FIGURES = {
    "fig:B1_BPGD_dec_order": (2, "b1", "bit_flip"),
    "fig:B1_BPGD_T": (3, "b1", "bit_flip"),
    "fig:B1_BPGD": (4, "b1", "bit_flip"),
    "fig:C2_BPGD": (5, "c2", "bit_flip"),
    "fig:B1_BPGD_rd_lim": (6, "b1", "bit_flip"),
    "fig:A5_QBPGD": (7, "a5", "depolarizing"),
    "fig:B2_QBPGD": (8, "b2", "depolarizing"),
}


def extract(archive: bytes) -> dict:
    if sha256(archive).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("arXiv source archive hash changed")
    with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as bundle:
        main = bundle.extractfile("main.tex")
        if main is None:
            raise ValueError("arXiv source lacks main.tex")
        tex_bytes = main.read()
    if sha256(tex_bytes).hexdigest() != TEX_SHA256:
        raise ValueError("arXiv main.tex hash changed")
    tex = tex_bytes.decode()
    figures = {}
    for body in re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", tex, re.S):
        match = re.search(r"\\label\{([^}]+)\}", body)
        if match is None or match.group(1) not in FIGURES:
            continue
        number, code, noise = FIGURES[match.group(1)]
        curves = {}
        excluded = []
        for data, legend in re.findall(
            r"\\addplot[^\n]*.*?table\s*\{%?\s*(.*?)\s*\};?\s*\\addlegendentry\{([^}]+)", body, re.S,
        ):
            pairs = re.findall(r"^\s*(0\.\d+)\s+(0\.\d+)", data, re.M)
            if len(pairs) != 7 and "BP-SI" not in legend:
                raise ValueError(f"unexpected point count in Figure {number}: {legend}")
            if "BP-OSD" in legend:
                excluded.append(legend)
                continue
            key = ("bp_si_external" if "BP-SI" in legend else
                   "bp" if legend == "BP" else
                   "qbp" if legend == "Q-BP" else
                   "bpgd_random_t100" if "rd-order" in legend else
                   "bpgd_t" + re.search(r"T\$?\s*=\s*(\d+)", legend).group(1) +
                   ("_r" + re.search(r"R\s*=\s*(\d+)", legend).group(1) if "R =" in legend else "")
                   if "BPGD" in legend else legend)
            if key in curves:
                raise ValueError(f"duplicate source curve {key} in Figure {number}")
            curves[key] = {f"{float(p):.5f}": float(rate) for p, rate in pairs}
        figures[str(number)] = {
            "label": match.group(1), "code": code, "noise": noise,
            "curves": curves, "excluded_bp_osd_curves": excluded,
        }
    if set(figures) != {"2", "3", "4", "5", "6", "7", "8"}:
        raise ValueError("not all non-OSD figures were extracted")
    return {
        "schema": "yao-2312-10950-non-osd-source-v1",
        "paper": "https://arxiv.org/pdf/2312.10950v2",
        "source_archive": URL,
        "archive_sha256": ARCHIVE_SHA256,
        "main_tex_sha256": TEX_SHA256,
        "figures": figures,
        "table_1": {
            "code": "b1", "metric": "mean_decimated_variables_including_nonconvergence",
            "p": [0.05, 0.06, 0.07, 0.08],
            "shots": [1000000, 100000, 100000, 10000],
            "mean": [2.91, 9.82, 60.46, 231.7],
            "iteration_conflict": "prose says T=10; caption says T=100",
        },
        "table_2": {
            "code": "b1", "physical_p": 0.08, "fixed_error_weight": 73,
            "randomized_trials": 10000, "converged": 9568, "distinct_corrections": 111,
            "source_error_bytes": "unpublished", "status": "exact_shot_blocked",
        },
        "source_conflicts": [
            "Figures 3 and 4 give different B1 T=10 values at every p; Figure 4 prose calls them identical.",
            "Table 1 prose assigns T=10 while its caption assigns T=100.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a local copy of the pinned arXiv source archive")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.read_bytes() if args.archive else urlopen(URL, timeout=30).read()
    args.output.write_text(json.dumps(extract(archive), indent=2, sort_keys=True) + "\n")
