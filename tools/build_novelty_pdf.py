#!/usr/bin/env python3
"""Render the living novelty register as a deterministic, source-hashed PDF."""

from __future__ import annotations

import argparse
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from build_docs_pdf import (
    BOTTOM,
    LEFT,
    LINE_HEIGHT,
    PAGE_SIZE,
    REPOSITORY_ROOT,
    TOP,
    SourceDocument,
    _configure_matplotlib,
    _line_style,
    _temporary_pdf_path,
    _wrapped_lines,
    validate_output,
)


SOURCE_RELATIVE = "docs/research-novelty-and-depth-register.md"
DEFAULT_OUTPUT = Path("docs/research-novelty-and-depth-register.pdf")
TITLE = "Research novelty and depth register"
PDF_METADATA = {
    "Title": TITLE,
    "Author": "Policy-Based BP Research Platform",
    "Subject": "Living provisional research-claim register",
    "Keywords": "QLDPC, BP, research, novelty, provisional",
    "Creator": "tools/build_novelty_pdf.py",
    "Producer": "Matplotlib PDF backend",
    "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
    "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
}


def _source() -> SourceDocument:
    path = REPOSITORY_ROOT / SOURCE_RELATIVE
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlinked novelty source: {SOURCE_RELATIVE}")
    payload = path.read_bytes()
    return SourceDocument(
        relative_path=SOURCE_RELATIVE,
        path=path.resolve(strict=True),
        sha256=hashlib.sha256(payload).hexdigest(),
        text=payload.decode("utf-8"),
    )


def _new_page(pdf: PdfPages, page_number: int):
    figure = plt.figure(figsize=PAGE_SIZE, dpi=72)
    figure.patch.set_facecolor("white")
    figure.text(LEFT, 0.965, TITLE, fontsize=8.5, family="DejaVu Sans", weight="bold", parse_math=False)
    figure.text(LEFT, 0.947, SOURCE_RELATIVE, fontsize=6.8, family="DejaVu Sans", color="#444444", parse_math=False)
    figure.text(LEFT, TOP, "Living provisional claims", fontsize=13.5, family="DejaVu Sans", weight="bold", va="top", parse_math=False)
    figure.text(LEFT, 0.045, f"Page {page_number}", fontsize=6.8, family="DejaVu Sans", color="#444444", parse_math=False)
    return figure, TOP - 0.035


def _render(output: Path, source: SourceDocument) -> None:
    _configure_matplotlib()
    lines = (
        "Source SHA-256: " + source.sha256,
        "Status: provisional research register; no entry establishes methodological novelty.",
        "The Markdown source is authoritative. This PDF is a readable rendering of that source.",
        "",
        *source.text.splitlines(),
    )
    with PdfPages(output, metadata=PDF_METADATA) as pdf:
        page_number = 1
        figure, y = _new_page(pdf, page_number)
        in_code_block = False
        for source_line in lines:
            style = _line_style(source_line, in_code_block)
            for visual_line in _wrapped_lines(source_line):
                if y < BOTTOM + LINE_HEIGHT:
                    pdf.savefig(figure, facecolor="white", edgecolor="white")
                    plt.close(figure)
                    page_number += 1
                    figure, y = _new_page(pdf, page_number)
                figure.text(
                    LEFT, y, visual_line, fontsize=style[1], family=style[0],
                    weight=style[2], va="top", parse_math=False,
                )
                y -= LINE_HEIGHT * (1.22 if style[2] == "bold" else 1.0)
            if source_line.startswith("```"):
                in_code_block = not in_code_block
        pdf.savefig(figure, facecolor="white", edgecolor="white")
        plt.close(figure)


def build_or_check(output: Path, *, check: bool) -> bool:
    source = _source()
    target = validate_output(output, (source,))
    temporary = _temporary_pdf_path(target)
    try:
        _render(temporary, source)
        if check:
            return target.is_file() and temporary.read_bytes() == target.read_bytes()
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
        return True
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
    try:
        matched = build_or_check(output, check=args.check)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    if args.check and not matched:
        print(f"PDF differs from current Markdown: {args.output}")
        return 1
    print(f"PDF {'matches' if args.check else 'written'}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
