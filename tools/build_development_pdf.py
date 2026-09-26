#!/usr/bin/env python3
"""Build/check the dated development report from a fixed, source-hashed inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

from build_docs_pdf import (
    REPOSITORY_ROOT, _configure_matplotlib, _resolve_sources,
    _temporary_pdf_path, validate_output,
)


TITLE = "BP platform: development and evidence"
DEFAULT_OUTPUT = Path("docs/development-update-20260926.pdf")
SOURCE_FILES = (
    "docs/development-update-20260926.md",
    "docs/phase4-plan-review-and-next-design.md",
    ".planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN.md",
    ".planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md",
)
EVIDENCE_FILES = (
    "docs/evidence/development-snapshot-20260926.json",
    "docs/evidence/phase4-low-noise-design-snapshot-20260926.json",
    "docs/evidence/phase5-source-status-20260926.json",
    "docs/evidence/intervention-design-validation-20260926.json",
)
HISTORICAL_PDFS = (
    "docs/policy-bp-documentation-through-phase-2.pdf",
    "docs/research-novelty-and-depth-register.pdf",
)
META = {
    "Title": "BP platform development update — 26 September 2026",
    "Author": "Policy-Based BP Research Platform",
    "Subject": "Phase 3–4 development, pending evidence and preparatory Phase 5 design",
    "Creator": "tools/build_development_pdf.py",
    "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
    "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
}
WIDTH, HEIGHT = 612.0, 792.0
LEFT, RIGHT, TOP, BOTTOM = 43.0, 569.0, 719.0, 56.0
BLUE, INK, MUTED = "#174a67", "#182a35", "#52616c"


def evidence_manifest():
    inventory = []
    for relative in EVIDENCE_FILES:
        path = REPOSITORY_ROOT / relative
        if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
            raise ValueError(f"unsafe or missing evidence input: {relative}")
        payload = path.read_bytes()
        json.loads(payload)
        inventory.append((relative, hashlib.sha256(payload).hexdigest()))
    return tuple(inventory)


def plain(text):
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return text.replace("**", "").replace("`", "")


class Renderer:
    def __init__(self, pdf, preview_dir=None):
        self.pdf = pdf
        self.preview_dir = preview_dir
        self.page = 0
        self.figure = None
        self.section = "Overview"
        self.drawn_text = []

    def text(self, x, y, value, *, size=9.5, weight="normal", color=INK, mono=False):
        obj = self.figure.text(x / WIDTH, y / HEIGHT, value, fontsize=size,
                                family="DejaVu Sans Mono" if mono else "DejaVu Sans",
                                weight=weight, color=color, va="top", parse_math=False)
        self.drawn_text.append(obj)

    @lru_cache(maxsize=32768)
    def measure(self, value, size=9.5, weight="normal", mono=False):
        font = FontProperties(family="DejaVu Sans Mono" if mono else "DejaVu Sans", size=size, weight=weight)
        return self.canvas.get_renderer().get_text_width_height_descent(value, font, False)[0]

    def wrap(self, value, width, *, size=9.5, weight="normal", mono=False):
        # Break long identities/URLs by measured width; preserve all characters.
        lines, current = [], ""
        for word in value.split():
            proposed = f"{current} {word}" if current else word
            if self.measure(proposed, size, weight, mono) <= width:
                current = proposed
                continue
            if current:
                lines.append(current)
                current = ""
            for char in word:
                if current and self.measure(current + char, size, weight, mono) > width:
                    lines.append(current)
                    current = ""
                current += char
        if current or not lines:
            lines.append(current)
        return lines

    def save(self):
        if self.figure is None:
            return
        # Inspect the same figures that are written to PDF; fail on clipped text.
        self.canvas.draw()
        renderer = self.canvas.get_renderer()
        for obj in self.drawn_text:
            box = obj.get_window_extent(renderer=renderer)
            if box.x0 < 30 or box.x1 > WIDTH - 30 or box.y0 < 20 or box.y1 > HEIGHT - 20:
                raise ValueError(f"text exceeds page bounds on page {self.page}: {obj.get_text()!r}")
        self.pdf.savefig(self.figure, facecolor="white", edgecolor="white")
        if self.preview_dir is not None:
            self.figure.savefig(self.preview_dir / f"page-{self.page:02d}.png", dpi=110, format="png")
        plt.close(self.figure)
        self.figure = None

    def new_page(self, section=None):
        self.save()
        if section is not None:
            self.section = section
        self.page += 1
        self.figure = plt.figure(figsize=(WIDTH / 72, HEIGHT / 72), dpi=72)
        self.canvas = FigureCanvasAgg(self.figure)
        self.figure.patch.set_facecolor("white")
        self.drawn_text = []
        self.text(LEFT, 762, TITLE, size=8.5, weight="bold", color=BLUE)
        self.text(LEFT, 745, self.section, size=7.8, color=MUTED)
        self.text(LEFT, 37, "26 September 2026 • frozen evidence snapshot • Phase 4 active", size=7, color=MUTED)
        self.text(RIGHT - 42, 37, f"Page {self.page}", size=7, color=MUTED)
        self.y = TOP

    def reserve(self, height):
        if self.y - height < BOTTOM:
            self.new_page()

    def paragraph(self, value, *, size=9.5, weight="normal", color=INK, mono=False, indent=0, after=7):
        lines = self.wrap(value, RIGHT - LEFT - indent, size=size, weight=weight, mono=mono)
        step = size * 1.45
        for line in lines:
            self.reserve(step)
            self.text(LEFT + indent, self.y, line, size=size, weight=weight, color=color, mono=mono)
            self.y -= step
        self.y -= after

    def heading(self, value, level):
        size = 17 if level == 1 else 12.2 if level == 2 else 10.6
        self.reserve(size * 1.5 + 40)
        self.y -= 5 if level > 1 else 0
        self.paragraph(plain(value), size=size, weight="bold", color=BLUE, after=9)

    def table(self, rows):
        # Fixed deterministic allocation, adjusted for the amount of cell text.
        weights = [max(9, min(28, max(len(row[i]) for row in rows))) for i in range(len(rows[0]))]
        full_width = RIGHT - LEFT
        widths = [full_width * weight / sum(weights) for weight in weights]
        size, step, pad = 8.0, 11.5, 5.0

        def render_row(row, header=False):
            wrapped = [self.wrap(plain(cell), width - 2 * pad, size=size, weight="bold" if header else "normal") for cell, width in zip(row, widths, strict=True)]
            height = max(len(cell) for cell in wrapped) * step + 2 * pad
            if height > TOP - BOTTOM - 60:
                raise ValueError("table row too tall for a page")
            if self.y - height < BOTTOM:
                self.new_page()
                if not header:
                    render_row(rows[0], header=True)
            self.figure.patches.append(plt.Rectangle((LEFT / WIDTH, (self.y - height) / HEIGHT), full_width / WIDTH, height / HEIGHT,
                                                      transform=self.figure.transFigure, facecolor="#e4eef4" if header else "#f5f8fa", edgecolor="white", linewidth=0.7))
            x = LEFT
            for cell, width in zip(wrapped, widths, strict=True):
                for line_number, line in enumerate(cell):
                    self.text(x + pad, self.y - pad - line_number * step, line, size=size, weight="bold" if header else "normal")
                x += width
            self.y -= height

        self.reserve(60)
        for i, row in enumerate(rows):
            render_row(row, header=i == 0)
        self.y -= 10

    def markdown(self, content):
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                self.heading(line[level:].strip(), level)
                i += 1
            elif line.startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    self.paragraph(lines[i], size=8.4, mono=True, indent=8, after=2)
                    i += 1
                i += 1
                self.y -= 6
            elif line.startswith("|"):
                table = []
                while i < len(lines) and lines[i].startswith("|"):
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in cells):
                        table.append(cells)
                    i += 1
                self.table(table)
            else:
                group = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```")) and not re.match(r"(?:- |\d+\. )", lines[i]):
                    group.append(lines[i])
                    i += 1
                self.paragraph(plain(" ".join(v.strip() for v in group)))


def render(output, sources, evidence, preview_dir):
    _configure_matplotlib()
    with PdfPages(output, metadata=META) as pdf:
        renderer = Renderer(pdf, preview_dir)
        renderer.new_page("Reader's guide and artifact provenance")
        renderer.heading("Development since the previous PDFs", 1)
        renderer.paragraph("26 September 2026", size=12, color=BLUE)
        renderer.paragraph("Completed code and finite computational evidence; active Phase 4 simulations; concrete design contracts for Phase 5.", size=11)
        renderer.heading("How to read this report", 2)
        renderer.paragraph("The narrative comes first. Appendices review the remaining plans and specify the next intervention contracts and task map. Proposed design, verified implementation and sampled performance retain different evidence statuses.")
        renderer.paragraph("Latest PDF baseline: novelty register, 24 September. Last broad technical snapshot: completed Phase 2, 23 September. Both historical PDFs are preserved.")
        renderer.heading("Fixed input inventory (SHA-256)", 2)
        for index, (name, digest) in enumerate([(s.relative_path, s.sha256) for s in sources] + list(evidence), 1):
            renderer.paragraph(f"{index}. {name}", size=8.4, after=2)
            renderer.paragraph(digest, size=7.8, mono=True, color=MUTED, after=7)
        renderer.paragraph("The Markdown files are editable sources. JSON inputs freeze observed status, source availability and algebra checks. Rebuilding does not read changing calibration files.", size=8.5)
        for source, section in zip(sources, ("Development narrative", "Appendix A • plan review", "Appendix B • Phase 5 contracts", "Appendix C • next task map"), strict=True):
            renderer.new_page(section)
            renderer.markdown(source.text)
        renderer.save()
        return renderer.page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preview-dir", type=Path, help="Optional PNG renderings of the same page figures")
    args = parser.parse_args()
    try:
        sources = _resolve_sources(REPOSITORY_ROOT, SOURCE_FILES)
        evidence = evidence_manifest()
        requested = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
        target = validate_output(requested, sources)
        if target in {(REPOSITORY_ROOT / name).resolve() for name in HISTORICAL_PDFS}:
            raise ValueError("historical PDF targets are protected")
        if args.preview_dir is not None:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
        temporary = _temporary_pdf_path(target)
        try:
            pages = render(temporary, sources, evidence, args.preview_dir)
            if args.check:
                if not target.is_file() or temporary.read_bytes() != target.read_bytes():
                    parser.exit(1, "PDF does not match its fixed source inventory\n")
            else:
                os.chmod(temporary, 0o644)
                os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f"PDF {'matches' if args.check else 'written'}: {target} ({pages} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
