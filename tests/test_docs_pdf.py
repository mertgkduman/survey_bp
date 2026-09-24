"""Focused regression tests for the Phase 1--2 PDF documentation snapshot."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import stat
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "tools" / "build_docs_pdf.py"
CHECKED_PDF = REPOSITORY_ROOT / "docs" / "policy-bp-documentation-through-phase-2.pdf"


def _load_renderer():
    spec = importlib.util.spec_from_file_location("build_docs_pdf", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def renderer():
    return _load_renderer()


def test_two_renders_are_identical_to_checked_snapshot_and_preserve_sources(renderer, tmp_path):
    sources = renderer.resolve_sources()
    before = {source.path: hashlib.sha256(source.path.read_bytes()).hexdigest() for source in sources}
    first = tmp_path / "first.pdf"

    renderer.build_pdf(first)

    assert first.read_bytes() == CHECKED_PDF.read_bytes()
    assert stat.S_IMODE(first.stat().st_mode) == 0o644
    assert renderer.check_pdf(CHECKED_PDF)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before


def test_snapshot_structure_inventory_and_evidence_limits(renderer):
    payload = CHECKED_PDF.read_bytes()
    manifest = renderer.source_manifest()

    assert payload.startswith(b"%PDF-")
    assert payload.rstrip().endswith(b"%%EOF")
    assert payload.count(b"/Type /Page") >= len(renderer.SOURCE_FILES) + 2
    assert [path for path, _ in manifest] == list(renderer.SOURCE_FILES)
    assert all(len(digest) == 64 for _, digest in manifest)
    assert all(not Path(path).is_absolute() for path, _ in manifest)
    front_matter = " ".join(renderer.FRONT_MATTER)
    assert "Phases 1 and 2 are complete" in front_matter
    assert "Phase 3 is not started" in front_matter
    assert "32-shot" in front_matter and "pilot_adaptation" in front_matter and "not_assessed" in front_matter
    assert "two-shot" in front_matter and "canonical_implemented" in front_matter and "development_fixture" in front_matter
    assert "source-faithful" in front_matter and "statistical reproduction" in front_matter


def test_invalid_sources_and_outputs_fail_before_replacement(renderer, monkeypatch, tmp_path):
    root = tmp_path / "repository"
    docs = root / "docs"
    docs.mkdir(parents=True)
    source = docs / "input.md"
    source.write_text("# Input\n", encoding="utf-8")
    output = tmp_path / "snapshot.pdf"
    output.write_bytes(b"keep-this-output")

    monkeypatch.setattr(renderer, "SOURCE_FILES", ("docs/missing.md",))
    with pytest.raises(ValueError, match="missing source Markdown"):
        renderer.build_pdf(output, root)
    assert output.read_bytes() == b"keep-this-output"

    linked = docs / "linked.md"
    linked.symlink_to(source)
    monkeypatch.setattr(renderer, "SOURCE_FILES", ("docs/linked.md",))
    with pytest.raises(ValueError, match="symlinked source"):
        renderer.resolve_sources(root)

    monkeypatch.setattr(renderer, "SOURCE_FILES", ("docs/input.md",))
    with pytest.raises(ValueError, match="must end in .pdf"):
        renderer.build_pdf(tmp_path / "snapshot.txt", root)
    with pytest.raises(ValueError, match="must end in .pdf"):
        renderer.build_pdf(source, root)

    pdf_input = docs / "input.pdf"
    pdf_input.write_bytes(b"not-a-real-pdf")
    source_document = renderer.SourceDocument("docs/input.pdf", pdf_input.resolve(), "0" * 64, "")
    with pytest.raises(ValueError, match="aliases input"):
        renderer.validate_output(pdf_input, (source_document,))


def test_public_renderer_rejects_an_alternate_source_inventory(renderer, tmp_path):
    """Only SOURCE_FILES may define the snapshot's evidence boundary."""

    with pytest.raises(TypeError):
        renderer.build_pdf(
            tmp_path / "unapproved.pdf",
            source_files=("docs/phase1-pilot.md",),
        )
