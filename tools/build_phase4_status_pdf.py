#!/usr/bin/env python3
"""Render/check the fixed 29 September Phase 4 update from Markdown and JSON."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages

from build_development_pdf import BLUE, Renderer
from build_docs_pdf import REPOSITORY_ROOT, _configure_matplotlib, _resolve_sources, _temporary_pdf_path, validate_output


SOURCE = "docs/development-update-20260929.md"
SNAPSHOT = "docs/evidence/phase4-status-snapshot-20260929.json"
DEFAULT_OUTPUT = Path("docs/development-update-20260929.pdf")
PROTECTED_OUTPUTS = (
    "docs/development-update-20260926.pdf",
    "docs/policy-bp-documentation-through-phase-2.pdf",
    "docs/research-novelty-and-depth-register.pdf",
)
META = {
    "Title": "BP platform development and evidence update — 29 September 2026",
    "Author": "Policy-Based BP Research Platform",
    "Subject": "Terminal Phase 4 calibration and remaining evaluation gates",
    "Creator": "tools/build_phase4_status_pdf.py",
    "CreationDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
    "ModDate": datetime(2000, 1, 1, tzinfo=timezone.utc),
}


def _snapshot(root: Path) -> tuple[bytes, dict]:
    path = root / SNAPSHOT
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents) or not path.is_file():
        raise ValueError("unsafe or absent fixed status snapshot")
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("unrecognized fixed status snapshot")
    if value.get("calibration", {}).get("retained_attempts") != 5824:
        raise ValueError("status snapshot does not describe the completed calibration")
    return raw, value


def render(output: Path, *, preview_dir: Path | None = None) -> int:
    source, = _resolve_sources(REPOSITORY_ROOT, (SOURCE,))
    snapshot_raw, snapshot = _snapshot(REPOSITORY_ROOT)
    _configure_matplotlib()
    with PdfPages(output, metadata=META) as pdf:
        renderer = Renderer(
            pdf, preview_dir, title="BP platform: development and evidence",
            footer="29 September 2026 • fixed evidence snapshot • Phase 4 active",
        )
        renderer.new_page("Reader's guide and provenance")
        renderer.heading("Development and evidence update", 1)
        renderer.paragraph("29 September 2026", size=12, color=BLUE)
        renderer.paragraph(
            "Calibration is terminal and independently audited. B1 remains inconclusive; fresh evaluation, factorial results and Phase 4 completion remain pending.",
            size=11,
        )
        renderer.heading("Fixed input inventory (SHA-256)", 2)
        renderer.paragraph(SOURCE, size=8.4, after=2)
        renderer.paragraph(source.sha256, size=7.8, mono=True, after=7)
        renderer.paragraph(SNAPSHOT, size=8.4, after=2)
        renderer.paragraph(sha256(snapshot_raw).hexdigest(), size=7.8, mono=True, after=7)
        renderer.paragraph(
            f"Captured {snapshot['captured_at_utc']}. The compact snapshot records hashes and counts from local raw campaign evidence; the large raw ledgers are not part of this PDF or documentation commit.",
            size=9,
        )
        renderer.paragraph(
            "Calibration estimates chose parameters and are not unbiased logical-error rates. The lower-noise CSS pilot is separate from the source paper's circuit-level experiments.",
            size=9,
        )
        renderer.new_page("29 September development update")
        renderer.markdown(source.text)
        renderer.save()
        return renderer.page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    try:
        source, = _resolve_sources(REPOSITORY_ROOT, (SOURCE,))
        _snapshot(REPOSITORY_ROOT)
        requested = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
        target = validate_output(requested, (source,))
        if target in {(REPOSITORY_ROOT / name).resolve() for name in PROTECTED_OUTPUTS}:
            raise ValueError("historical PDF targets are protected")
        if args.preview_dir is not None:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
        temporary = _temporary_pdf_path(target)
        try:
            pages = render(temporary, preview_dir=args.preview_dir)
            if args.check:
                if not target.is_file() or temporary.read_bytes() != target.read_bytes():
                    parser.exit(1, "PDF differs from fixed Markdown and snapshot bytes\n")
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
