#!/usr/bin/env python3
"""Build the deterministic Phase 1--2 documentation PDF snapshot.

The Markdown files named in ``SOURCE_FILES`` remain the source of truth.  This
small renderer deliberately lays their text out as text; it is not a Markdown,
HTML, or TeX conversion pipeline. The canonical-engine input is frozen at the
Phase 2 boundary so later phase documentation does not change this snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("pdf", force=True)
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("docs/policy-bp-documentation-through-phase-2.pdf")
SOURCE_FILES: tuple[str, ...] = (
    "docs/phase1-source-decisions.md",
    "docs/environment-pins.md",
    "docs/phase1-pilot.md",
    ".planning/phases/01-evidence-registry-and-native-css-baseline/01-VERIFICATION.md",
    "docs/snapshots/canonical-engine-through-phase-2.md",
    "docs/profiling-and-tracing-strategy.md",
    "docs/snapshots/research-novelty-and-depth-register-through-phase-2.md",
    ".planning/phases/02-canonical-css-execution-and-policy-contracts/02-VERIFICATION.md",
)
SECTION_TITLES: tuple[str, ...] = (
    "Phase 1 source decisions",
    "Development environment",
    "Phase 1 native CSS pilot",
    "Phase 1 verification",
    "Canonical CSS engine",
    "Profiling and tracing",
    "Research novelty and depth",
    "Phase 2 verification",
)

FRONT_MATTER: tuple[str, ...] = (
    "Status and evidence limits",
    "Phases 1 and 2 are complete. Phase 3 is not started and is outside this snapshot.",
    "Phase 1 is a 32-shot native-BP pilot_adaptation / not_assessed result, not an impulse-paper reproduction.",
    "Phase 2 is a two-shot canonical_implemented / development_fixture / not_assessed result, not a source-faithful or statistical reproduction.",
    "Profiling, tracing, and novelty entries remain provisional.",
    "The verification reports, not this PDF, are the executable evidence authority.",
    "This PDF is a portable rendering of the listed repository Markdown sources; source labels and SHA-256 digests below provide provenance.",
)

PDF_METADATA = {
    "Title": "Policy-Based BP Documentation through Phase 2",
    "Author": "Policy-Based BP Research Platform",
    "Subject": "Repository documentation snapshot with evidence limits",
    "Keywords": "QLDPC, BP, documentation, Phase 1, Phase 2",
    "Creator": "tools/build_docs_pdf.py",
    "Producer": "Matplotlib PDF backend",
    "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
    "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
}

PAGE_SIZE = (8.5, 11.0)
LEFT = 0.065
RIGHT = 0.935
TOP = 0.925
BOTTOM = 0.075
LINE_HEIGHT = 0.0143
WRAP_WIDTH = 104


@dataclass(frozen=True)
class SourceDocument:
    """A validated source document and its repository-relative digest."""

    relative_path: str
    path: Path
    sha256: str
    text: str


@dataclass
class RenderState:
    """The deterministic page counter shared by all document sections."""

    page_number: int = 0


def _relative_source_path(relative_path: str) -> PurePosixPath:
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"source path must be repository-relative: {relative_path!r}")
    return relative


def _has_symlinked_component(root: Path, relative: PurePosixPath) -> bool:
    candidate = root
    for component in relative.parts:
        candidate = candidate / component
        if candidate.is_symlink():
            return True
    return False


def _resolve_sources(
    repository_root: Path = REPOSITORY_ROOT,
    source_files: Sequence[str] = SOURCE_FILES,
) -> tuple[SourceDocument, ...]:
    """Return the fixed input inventory after rejecting unsafe source paths."""

    root = Path(repository_root).resolve(strict=True)
    documents: list[SourceDocument] = []
    seen: set[str] = set()
    for source_name in source_files:
        relative = _relative_source_path(source_name)
        label = relative.as_posix()
        if label in seen:
            raise ValueError(f"duplicate source path: {label}")
        seen.add(label)
        candidate = root.joinpath(*relative.parts)
        if _has_symlinked_component(root, relative):
            raise ValueError(f"symlinked source is not allowed: {label}")
        if not candidate.is_file():
            raise ValueError(f"missing source Markdown: {label}")
        if candidate.suffix.lower() != ".md":
            raise ValueError(f"source is not Markdown: {label}")
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise ValueError(f"source escapes repository root: {label}") from error
        payload = resolved.read_bytes()
        documents.append(
            SourceDocument(
                relative_path=label,
                path=resolved,
                sha256=hashlib.sha256(payload).hexdigest(),
                text=payload.decode("utf-8"),
            )
        )
    return tuple(documents)


def resolve_sources(repository_root: Path = REPOSITORY_ROOT) -> tuple[SourceDocument, ...]:
    """Return the immutable, approved documentation inventory."""

    return _resolve_sources(repository_root, SOURCE_FILES)


def source_manifest(repository_root: Path = REPOSITORY_ROOT) -> tuple[tuple[str, str], ...]:
    """Return ordered, repository-relative source labels and SHA-256 values."""

    return tuple((source.relative_path, source.sha256) for source in resolve_sources(repository_root))


def validate_output(output: Path, sources: Iterable[SourceDocument]) -> Path:
    """Validate a local output target before creating or replacing anything."""

    requested = Path(output)
    if requested.suffix.lower() != ".pdf":
        raise ValueError("output path must end in .pdf")
    if requested.exists() and requested.is_symlink():
        raise ValueError("output path must not be a symlink")
    parent = requested.parent
    if not parent.is_dir():
        raise ValueError(f"output directory does not exist: {parent}")
    if parent.is_symlink():
        raise ValueError("output directory must not be a symlink")
    output_path = requested.resolve(strict=False)
    if requested.exists() and not requested.is_file():
        raise ValueError("output path must be a regular file")
    for source in sources:
        if output_path == source.path:
            raise ValueError(f"output path aliases input source: {source.relative_path}")
    return output_path


def _line_style(line: str, in_code_block: bool) -> tuple[str, float, str]:
    if in_code_block or line.startswith("```"):
        return ("DejaVu Sans Mono", 7.1, "normal")
    if line.startswith("#"):
        level = min(len(line) - len(line.lstrip("#")), 3)
        return ("DejaVu Sans", 12.5 - level * 1.2, "bold")
    if line.startswith("|") or line.lstrip().startswith(("- ", "* ", "+ ", "1. ")):
        return ("DejaVu Sans", 8.0, "normal")
    return ("DejaVu Sans", 8.4, "normal")


def _wrapped_lines(line: str, width: int = WRAP_WIDTH) -> tuple[str, ...]:
    if not line:
        return ("",)
    initial_indent = ""
    stripped = line.lstrip(" ")
    if stripped != line:
        initial_indent = line[: len(line) - len(stripped)]
    wrapped = textwrap.wrap(
        line,
        width=width,
        subsequent_indent=initial_indent,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )
    return tuple(wrapped) if wrapped else ("")


def _new_page(pdf: PdfPages, state: RenderState, label: str, title: str):
    state.page_number += 1
    figure = plt.figure(figsize=PAGE_SIZE, dpi=72)
    figure.patch.set_facecolor("white")
    figure.text(LEFT, 0.965, "Policy-Based BP Documentation through Phase 2", fontsize=8.5, family="DejaVu Sans", weight="bold", parse_math=False)
    figure.text(LEFT, 0.947, label, fontsize=6.8, family="DejaVu Sans", color="#444444", parse_math=False)
    figure.text(LEFT, TOP, title, fontsize=13.5, family="DejaVu Sans", weight="bold", va="top", parse_math=False)
    figure.text(LEFT, 0.045, f"Page {state.page_number}", fontsize=6.8, family="DejaVu Sans", color="#444444", parse_math=False)
    return figure, TOP - 0.035


def _save_page(pdf: PdfPages, figure) -> None:
    pdf.savefig(figure, facecolor="white", edgecolor="white")
    plt.close(figure)


def _render_text_section(
    pdf: PdfPages,
    state: RenderState,
    label: str,
    title: str,
    lines: Sequence[str],
) -> None:
    figure, y = _new_page(pdf, state, label, title)
    in_code_block = False
    for source_line in lines:
        style = _line_style(source_line, in_code_block)
        for visual_line in _wrapped_lines(source_line):
            if y < BOTTOM + LINE_HEIGHT:
                _save_page(pdf, figure)
                figure, y = _new_page(pdf, state, label, f"{title} (continued)")
            figure.text(LEFT, y, visual_line, fontsize=style[1], family=style[0], weight=style[2], va="top", parse_math=False)
            y -= LINE_HEIGHT * (1.22 if style[2] == "bold" else 1.0)
        if source_line.startswith("```"):
            in_code_block = not in_code_block
    _save_page(pdf, figure)


def _render_front_matter(pdf: PdfPages, state: RenderState, sources: Sequence[SourceDocument]) -> None:
    manifest_lines = [
        "Contents and source manifest",
        "The following sections are rendered in this fixed order. Each digest is SHA-256 over the source Markdown bytes.",
        "",
    ]
    manifest_lines.extend(f"{index}. {source.relative_path}  {source.sha256}" for index, source in enumerate(sources, start=1))
    _render_text_section(pdf, state, "Front matter", FRONT_MATTER[0], FRONT_MATTER[1:])
    _render_text_section(pdf, state, "Front matter", manifest_lines[0], manifest_lines[1:])


def _configure_matplotlib() -> None:
    matplotlib.rcParams.update(
        {
            "pdf.compression": 0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.family": "DejaVu Sans",
            "savefig.dpi": 72,
        }
    )


def render_pdf(
    output: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> Path:
    """Render the fixed inventory to ``output`` without replacing it yet."""

    sources = resolve_sources(repository_root)
    output_path = validate_output(output, sources)
    _configure_matplotlib()
    state = RenderState()
    with PdfPages(output_path, metadata=PDF_METADATA) as pdf:
        _render_front_matter(pdf, state, sources)
        for source, title in zip(sources, SECTION_TITLES, strict=True):
            _render_text_section(
                pdf,
                state,
                source.relative_path,
                title,
                source.text.splitlines(),
            )
    return output_path


def _temporary_pdf_path(output_path: Path) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".pdf", dir=output_path.parent)
    os.close(descriptor)
    return Path(raw_path)


def build_pdf(
    output: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> Path:
    """Atomically render and replace the approved output PDF."""

    sources = resolve_sources(repository_root)
    output_path = validate_output(output, sources)
    temporary_path = _temporary_pdf_path(output_path)
    try:
        render_pdf(temporary_path, repository_root)
        # mkstemp creates mode 0600; this checked-in documentation is meant to
        # be readable by collaborators on the shared filesystem.
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output_path


def check_pdf(
    output: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> bool:
    """Render beside ``output`` and compare the result byte-for-byte."""

    sources = resolve_sources(repository_root)
    output_path = validate_output(output, sources)
    if not output_path.is_file():
        return False
    temporary_path = _temporary_pdf_path(output_path)
    try:
        render_pdf(temporary_path, repository_root)
        return temporary_path.read_bytes() == output_path.read_bytes()
    finally:
        temporary_path.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PDF path, relative to the repository root by default")
    parser.add_argument("--check", action="store_true", help="fail unless a fresh deterministic render byte-matches --output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
    try:
        if args.check:
            if check_pdf(output):
                print(f"PDF snapshot matches: {args.output}")
                return 0
            print(f"PDF snapshot differs or is missing: {args.output}")
            return 1
        build_pdf(output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}")
        return 2
    print(f"PDF snapshot written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
