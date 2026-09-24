"""Execute the confined Phase 3 evidence-only notebook with the project venv."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ANALYSIS_VERSIONS = {
    "matplotlib": "3.10.9",
    "nbformat": "5.10.4",
    "nbclient": "0.10.2",
    "ipykernel": "6.29.5",
}


def _confined_path(repository_root: Path, value: str, *, required_parent: Path) -> Path:
    """Resolve a user path only when it remains below its declared project root."""
    candidate = Path(value)
    path = (repository_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        path.relative_to(required_parent.resolve())
    except ValueError as error:
        raise ValueError(f"path must be confined below {required_parent}: {path}") from error
    return path


def _assert_project_interpreter(repository_root: Path) -> Path:
    expected = repository_root / ".venv" / "bin" / "python"
    actual = Path(sys.executable)
    if actual.resolve() != expected.resolve():
        raise RuntimeError(f"project interpreter required: expected {expected.resolve()}, got {actual.resolve()}")
    # Keep the project-local spelling in the kernelspec: resolving the venv
    # symlink launches the base interpreter and loses its venv site-packages.
    return actual


def _assert_analysis_versions() -> None:
    observed = {package: version(package) for package in ANALYSIS_VERSIONS}
    if observed != ANALYSIS_VERSIONS:
        raise RuntimeError(f"analysis dependency versions drifted: {observed}")


def execute_notebook(*, repository_root: Path, input_path: str, output_path: str) -> Path:
    """Execute a source notebook without permitting it to leave D-18 roots."""
    repository_root = repository_root.resolve()
    interpreter = _assert_project_interpreter(repository_root)
    _assert_analysis_versions()
    notebook_root = repository_root / "notebooks"
    result_root = repository_root / "data" / "results" / "phase3-pilots"
    source = _confined_path(repository_root, input_path, required_parent=notebook_root)
    destination = _confined_path(repository_root, output_path, required_parent=result_root)
    if source == destination:
        raise ValueError("source and executed notebook paths must differ")
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    notebook = nbformat.read(source, as_version=4)
    with tempfile.TemporaryDirectory(prefix="phase3-kernel-") as temporary:
        kernels_root = Path(temporary) / "kernels" / "phase3-project"
        kernels_root.mkdir(parents=True)
        (kernels_root / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [str(interpreter), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "Phase 3 project venv",
                    "language": "python",
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["JUPYTER_PATH"] = temporary
        environment["MPLBACKEND"] = "Agg"
        environment["PHASE3_REPOSITORY_ROOT"] = str(repository_root)
        client = NotebookClient(
            notebook,
            kernel_name="phase3-project",
            timeout=120,
            allow_errors=False,
            resources={"metadata": {"path": str(repository_root)}},
        )
        previous = os.environ.copy()
        os.environ.update(environment)
        try:
            client.execute(cwd=str(repository_root))
        finally:
            os.environ.clear()
            os.environ.update(previous)
    nbformat.write(notebook, destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[1]
    executed = execute_notebook(
        repository_root=repository_root,
        input_path=args.input,
        output_path=args.output,
    )
    print(executed.relative_to(repository_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
