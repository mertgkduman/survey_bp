#!/usr/bin/env python3
"""Execute the read-only Phase 5 notebook from digest-checked retained evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.phase5_analysis import load_verified_evidence  # noqa: E402


def execute_notebook(evidence: Path, output: Path) -> Path:
    dataset = load_verified_evidence(evidence)
    source = ROOT / "notebooks/phase5-interventions-analysis.ipynb"
    notebook = nbformat.read(source, as_version=4)
    tagged = [cell for cell in notebook.cells if "phase5_parameters" in cell.metadata.get("tags", ())]
    if len(tagged) != 1:
        raise ValueError("Phase 5 notebook requires one parameter cell")
    tagged[0].source = (
        "from pathlib import Path\n"
        f"EVIDENCE_ROOT = Path({json.dumps(str(Path(evidence).resolve(strict=True)))})\n"
        "SHOT_ID = 0\n"
        "SELECTED_ARM = 'guided_decimation'\n"
    )
    notebook.metadata["phase5_evidence"] = {
        "ledger_sha256": dataset.ledger_sha256,
        "design_digest": dataset.design_digest,
        "assessment_status": dataset.assessment_status,
        "source_root": str(Path(evidence).resolve(strict=True)),
        "source_notebook_sha256": sha256(source.read_bytes()).hexdigest(),
    }
    # The generic python3 kernelspec resolves `python` from PATH.  Bind it to
    # this project's pinned environment, then restore the caller environment.
    old_path = os.environ.get("PATH", "")
    old_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + old_path
    os.environ["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT), old_pythonpath or ""))
    try:
        client = NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
        executed = client.execute()
    finally:
        os.environ["PATH"] = old_path
        if old_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = old_pythonpath
    for cell in executed.cells:
        cell.metadata.pop("execution", None)
        if cell.cell_type == "code":
            cell.execution_count = None
            for item in cell.get("outputs", []):
                item.pop("execution_count", None)
    executed.metadata.pop("language_info", None)
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(executed, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(execute_notebook(args.evidence, args.output))


if __name__ == "__main__":
    main()
