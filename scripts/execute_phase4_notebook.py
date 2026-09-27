"""Execute the confined Phase 4 notebook; --fixture tests plumbing only."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from phase4_notebook_support import confined, validate_environment


def project_interpreter(root: Path) -> Path:
    expected = root / ".venv/bin/python"
    if not expected.exists() and (root / ".git").is_file():
        # Existing GSD worktrees share the primary checkout's qualified venv.
        common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=root,
                                check=True, capture_output=True, text=True).stdout.strip()
        git_directory = (root / common).resolve()
        expected = git_directory.parent / ".venv/bin/python"
    if Path(sys.executable).absolute() != expected.absolute():
        raise RuntimeError(f"project interpreter required: {expected}")
    return expected


def campaign_input_root(root: Path, requested: Path | None = None) -> Path:
    """Allow read-only evidence from the same repository's primary/worktree roots."""
    candidate = root.resolve() if requested is None else requested.resolve()
    if candidate == root.resolve():
        return candidate
    def repository_identity(directory: Path) -> Path:
        result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=directory,
                                check=True, capture_output=True, text=True)
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=directory,
                             check=True, capture_output=True, text=True)
        if Path(top.stdout.strip()).resolve() != directory:
            raise ValueError("campaign input must be a repository root")
        return (directory / result.stdout.strip()).resolve()
    try:
        if repository_identity(root.resolve()) != repository_identity(candidate):
            raise ValueError("campaign input must belong to the same Git repository")
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("campaign input must belong to the same Git repository") from error
    return candidate


def execute_notebook(*, repository_root: Path, input_path: str, output_path: str,
                     fixture: bool = False, campaign_root: Path | None = None) -> Path:
    root = repository_root.resolve()
    expected = project_interpreter(root)
    validate_environment()
    evidence_root = campaign_input_root(root, campaign_root)
    source = confined(root, input_path, "notebooks")
    destination = confined(root, output_path, "data/results/phase4-notebook")
    if source == destination:
        raise ValueError("source and executed notebook must differ")
    notebook = nbformat.read(source, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    with tempfile.TemporaryDirectory(prefix="phase4-kernel-") as temporary:
        kernel = Path(temporary) / "kernels/phase4-project"
        kernel.mkdir(parents=True)
        (kernel / "kernel.json").write_text(json.dumps({
            "argv": [str(expected), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Phase 4 project venv", "language": "python",
        }), encoding="utf-8")
        manager = KernelManager(kernel_name="phase4-project", kernel_spec_manager=
                                KernelSpecManager(kernel_dirs=[str(Path(temporary) / "kernels")]))
        # Retained campaign validation includes CSS algebra and complete ledgers;
        # the measured inventory takes several minutes, without running simulations.
        client = NotebookClient(notebook, km=manager, kernel_name="phase4-project", timeout=120 if fixture else 600,
                                allow_errors=False, resources={"metadata": {"path": str(root)}})
        try:
            client.execute(cwd=str(root), env={**os.environ, "JUPYTER_PATH": temporary,
                           "MPLBACKEND": "Agg", "OMP_NUM_THREADS": "1",
                           "PHASE4_REPOSITORY_ROOT": str(root),
                           "PHASE4_CAMPAIGN_ROOT": str(evidence_root),
                           "PHASE4_NOTEBOOK_FIGURE_ROOT": str(destination.parent / "figures"),
                           "PHASE4_NOTEBOOK_FIXTURE": "1" if fixture else "0"})
        finally:
            # An explicitly supplied manager is caller-owned in nbclient.
            if client.kc is not None:
                client.kc.stop_channels()
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            manager.cleanup_resources()
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
    notebook.metadata["phase4_validation"] = {
        "mode": "development_fixture" if fixture else "qualified_snapshot_inventory",
        "assessment_status": "not_assessed", "production_sampling": False,
        "campaign_input_root": str(evidence_root),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="notebooks/phase4-memory-relay-analysis.ipynb")
    parser.add_argument("--output", default="data/results/phase4-notebook/executed.ipynb")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--campaign-root", type=Path,
                        help="Read evidence from this repository's primary or worktree root")
    args = parser.parse_args()
    print(execute_notebook(repository_root=Path(__file__).resolve().parents[1],
                           input_path=args.input, output_path=args.output, fixture=args.fixture,
                           campaign_root=args.campaign_root))


if __name__ == "__main__":
    main()
