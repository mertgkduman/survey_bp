#!/usr/bin/env python3
"""Build/check the dated, color-coded study-design glossary PDF from Markdown."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re

from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from build_development_pdf import BLUE, INK, LEFT, RIGHT, WIDTH, HEIGHT, BOTTOM, TOP, Renderer
from build_docs_pdf import (
    REPOSITORY_ROOT,
    _configure_matplotlib,
    _resolve_sources,
    _temporary_pdf_path,
    validate_output,
)


SOURCE = "docs/study-design-glossary.md"
DEFAULT_OUTPUT = Path("docs/study-design-glossary.pdf")
STATUS = {
    "Executed": ("#176247", "#E8F4EE"),
    "On hold": ("#945B00", "#FFF2D6"),
    "Future": ("#1D598B", "#E9F2FB"),
}
META = {
    "Title": "Study-design glossary and work status — 30 September 2026",
    "Author": "Policy-Based BP Research Platform",
    "Subject": "Source-backed design terms and executed, on-hold, and future work",
    "Creator": "tools/build_study_design_glossary_pdf.py",
    "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
    "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
}
LINK = re.compile(r"\[([^]]+)\]\(([^)]+)\)")
ICON = re.compile(r"[🟩🟨🟦]")


def display(value: str) -> str:
    """Use the Markdown's human label in the PDF and draw status color separately."""
    value = LINK.sub(r"\1", value)
    value = ICON.sub("", value)
    return value.replace("**", "").replace("`", "").strip()


def status_of(value: str) -> str | None:
    label = display(value)
    return label if label in STATUS else None


def parse_sections(markdown: str) -> list[tuple[str, object]]:
    """Read the source's level-two headings, paragraphs, and four-column tables."""
    lines = markdown.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## Study sequence at a glance")), None)
    if start is None:
        raise ValueError("study sequence heading is missing")
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## Rebuild and provenance")), len(lines))
    items: list[tuple[str, object]] = []
    i = start
    while i < end:
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("## "):
            items.append(("heading", display(line[3:])))
            i += 1
            continue
        if line.startswith("|"):
            rows: list[list[str]] = []
            while i < end and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in cells):
                    if len(cells) != 4:
                        raise ValueError(f"expected four table columns: {lines[i]}")
                    rows.append(cells)
                i += 1
            if len(rows) < 2:
                raise ValueError("a glossary table has no entries")
            for row in rows[1:]:
                if status_of(row[1]) is None:
                    raise ValueError(f"missing status label for {row[0]}")
            items.append(("table", rows))
            continue
        paragraph = [line]
        i += 1
        while i < end and lines[i].strip() and not lines[i].startswith(("## ", "|")):
            paragraph.append(lines[i].strip())
            i += 1
        items.append(("paragraph", display(" ".join(paragraph))))
    return items


class GlossaryRenderer(Renderer):
    """Status-aware table rendering with text labels and high-contrast color."""

    def table(self, rows: list[list[str]]) -> None:
        widths = [126.0, 76.0, 250.0, 74.0]
        if abs(sum(widths) - (RIGHT - LEFT)) > 0.01:
            raise ValueError("table columns do not fill the text area")
        font_size = 8.2
        line_step = 11.3
        pad = 5.5

        def row(cells: list[str], *, header: bool = False) -> None:
            labels = [display(cell) for cell in cells]
            wrapped = [
                self.wrap(label, width - 2 * pad, size=font_size,
                          weight="bold" if header or index == 0 else "normal")
                for index, (label, width) in enumerate(zip(labels, widths, strict=True))
            ]
            height = max(len(cell) for cell in wrapped) * line_step + 2 * pad
            if height > TOP - BOTTOM - 50:
                raise ValueError(f"glossary entry exceeds one page: {labels[0]}")
            if self.y - height < BOTTOM:
                self.new_page()
                if not header:
                    row(rows[0], header=True)
            status = None if header else status_of(cells[1])
            pale = STATUS[status][1] if status else "#E4EEF4"
            self.figure.patches.append(
                plt.Rectangle(
                    (LEFT / WIDTH, (self.y - height) / HEIGHT),
                    (RIGHT - LEFT) / WIDTH, height / HEIGHT,
                    transform=self.figure.transFigure, facecolor=pale,
                    edgecolor="white", linewidth=0.75,
                )
            )
            if status:
                x_status = LEFT + widths[0]
                self.figure.patches.append(
                    plt.Rectangle(
                        (x_status / WIDTH, (self.y - height) / HEIGHT),
                        widths[1] / WIDTH, height / HEIGHT,
                        transform=self.figure.transFigure,
                        facecolor=STATUS[status][0], edgecolor="white", linewidth=0.75,
                    )
                )
            x = LEFT
            for index, (cell_lines, width) in enumerate(zip(wrapped, widths, strict=True)):
                color = "white" if status and index == 1 else INK
                for line_number, text_line in enumerate(cell_lines):
                    self.text(
                        x + pad, self.y - pad - line_number * line_step, text_line,
                        size=font_size, weight="bold" if header or index in (0, 1) else "normal",
                        color=color,
                    )
                x += width
            self.y -= height

        self.reserve(65)
        for index, cells in enumerate(rows):
            row(cells, header=index == 0)
        self.y -= 9


def render(output: Path, source_text: str, source_digest: str, preview_dir: Path | None) -> int:
    _configure_matplotlib()
    with PdfPages(output, metadata=META) as pdf:
        renderer = GlossaryRenderer(
            pdf, preview_dir, title="BP platform: study-design glossary",
            footer="30 September 2026  •  status snapshot  •  color plus text labels",
        )
        renderer.new_page("Reader's guide")
        renderer.heading("Study-design glossary and work status", 1)
        renderer.paragraph("30 September 2026", size=12, color=BLUE)
        renderer.paragraph(
            "The first journal milestone covers CSS code-capacity, correlated quaternary code-capacity, and circuit-level decoding in sequence. This glossary separates completed implementation and evidence from cancelled or inconclusive work and planned research.",
            size=10.4,
        )
        renderer.heading("Status key", 2)
        legend = (
            ("Executed", "Implemented, run, or checked at the scope stated; a pilot is not automatically a paper reproduction."),
            ("On hold", "Cancelled, inconclusive, or awaiting a source qualification; retained partial evidence remains visible."),
            ("Future", "Designed or required, but not yet implemented or assessed at this scope."),
        )
        for label, meaning in legend:
            renderer.reserve(49)
            color, pale = STATUS[label]
            renderer.figure.patches.append(
                plt.Rectangle(
                    (LEFT / WIDTH, (renderer.y - 34) / HEIGHT), 96 / WIDTH, 34 / HEIGHT,
                    transform=renderer.figure.transFigure, facecolor=color, edgecolor=color,
                )
            )
            renderer.figure.patches.append(
                plt.Rectangle(
                    ((LEFT + 96) / WIDTH, (renderer.y - 34) / HEIGHT),
                    (RIGHT - LEFT - 96) / WIDTH, 34 / HEIGHT,
                    transform=renderer.figure.transFigure, facecolor=pale, edgecolor="white",
                )
            )
            renderer.text(LEFT + 7, renderer.y - 8, label.upper(), size=8.8, weight="bold", color="white")
            wrapped = renderer.wrap(meaning, RIGHT - LEFT - 111, size=8.8)
            for n, line in enumerate(wrapped):
                renderer.text(LEFT + 106, renderer.y - 6 - n * 12.2, line, size=8.8)
            renderer.y -= 47
        renderer.heading("Source and claim boundary", 2)
        renderer.paragraph(
            "The editable Markdown contains direct repository links. This PDF is a dated rendering of those definitions; future phase plans are intentions, not completed experiments. Phase 4's cancelled comprehensive campaign is retained only as partial evidence.",
            size=9.5,
        )
        renderer.paragraph("Markdown SHA-256: " + source_digest, size=7.8, mono=True, color=BLUE)

        for kind, value in parse_sections(source_text):
            if kind == "heading":
                renderer.section = str(value)
                renderer.heading(str(value), 2)
            elif kind == "paragraph":
                renderer.paragraph(str(value), size=9)
            else:
                renderer.table(value)

        links = list(dict.fromkeys(target for _, target in LINK.findall(source_text)))
        renderer.new_page("Source index")
        renderer.heading("Source index", 2)
        renderer.paragraph("The editable Markdown provides direct links. These are the unique repository files cited by the glossary.", size=9)
        for target in links:
            renderer.paragraph(target, size=7.8, after=3)
        renderer.save()
        return renderer.page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="verify byte-for-byte regenerated PDF")
    parser.add_argument("--preview-dir", type=Path, help="optional PNG pages for visual inspection")
    args = parser.parse_args()
    try:
        source, = _resolve_sources(REPOSITORY_ROOT, (SOURCE,))
        requested = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
        target = validate_output(requested, (source,))
        if args.preview_dir is not None:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
        temporary = _temporary_pdf_path(target)
        try:
            pages = render(temporary, source.text, source.sha256, args.preview_dir)
            if args.check:
                if not target.is_file() or temporary.read_bytes() != target.read_bytes():
                    parser.exit(1, "PDF differs from the Markdown source\n")
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
