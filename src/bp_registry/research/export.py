"""Portable, inspectable experiment bundles shared with the static interface."""

from __future__ import annotations

from hashlib import sha256, file_digest
import json
from pathlib import Path
from typing import Any
import zipfile


RUN_SCRIPT = '''"""Execute this package with the installed survey_bp implementation."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256, file_digest
import json
from pathlib import Path
import sys
import uuid

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="survey_bp checkout (optional with an editable installation)")
    parser.add_argument("--output", type=Path, help="new output directory; existing output is never overwritten")
    parser.add_argument("--validate-only", action="store_true", help="validate without sampling")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "package-manifest.json").read_text())
    for name, expected in manifest["files"].items():
        path = root / name
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError("invalid package member path")
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Package file changed: {name}. Export again after editing the specification.")
    if args.repo is not None:
        repo = args.repo.expanduser().resolve()
        if not (repo / "src/bp_registry").is_dir():
            parser.error("--repo must identify a survey_bp checkout")
        sys.path.insert(0, str(repo / "src"))
    else:
        repo = None
    from bp_registry.research.runner import run_experiment
    from bp_registry.research.contracts import validate_experiment
    spec = json.loads((root / "experiment.json").read_text())
    if args.validate_only:
        validated = validate_experiment(spec, repository=repo)
        if hasattr(validated, "model_dump"):
            validated = validated.model_dump(mode="json", by_alias=True)
        print(json.dumps(validated, indent=2, default=str))
        return
    output = args.output or root / "results" / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    result = run_experiment(spec, output=output, repository=repo)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
'''

ANALYSIS_SCRIPT = '''"""Plot measured output from a downloaded research experiment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from hashlib import sha256, file_digest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="directory containing summary.json")
    parser.add_argument("--output", type=Path, help="new PNG filename")
    args = parser.parse_args()
    manifest_path = args.results / "result-manifest.json"
    if manifest_path.exists():
        for name, expected in json.loads(manifest_path.read_text())["files"].items():
            candidate = (args.results / name).resolve()
            if not candidate.is_relative_to(args.results.resolve()) or candidate.is_symlink():
                raise ValueError("invalid result manifest member")
            with candidate.open("rb") as handle:
                actual_digest = file_digest(handle, "sha256").hexdigest()
            if actual_digest != expected:
                raise ValueError(f"Result file changed: {name}")
    payload = json.loads((args.results / "summary.json").read_text())
    rows = payload.get("rows", payload.get("points", payload.get("results", [])))
    if isinstance(rows, dict):
        rows = list(rows.values())
    if not rows:
        raise ValueError("summary.json contains no measured rows")
    print(json.dumps(rows, indent=2))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output = args.output or args.results / "failure-rate.png"
    if output.exists():
        raise FileExistsError(output)
    x = []
    physical_axis = any(isinstance(row.get("p"), (int, float)) for row in rows)
    prior_axis = not physical_axis and any(isinstance(row.get("decoder_p0"), (int, float)) for row in rows)
    for i, row in enumerate(rows):
        value = row.get("p", row.get("physical_error_rate"))
        x.append(value if isinstance(value, (int, float)) else row.get("decoder_p0") if prior_axis else i)
    y = [row.get("ler") if isinstance(row.get("ler"), (int, float)) else
         row.get("failure_rate", row.get("rate_estimate", 0)) for row in rows]
    fig, ax = plt.subplots(figsize=(7, 4))
    plotted = []
    for i, row in enumerate(rows):
        low = row.get("ci_low", row.get("ci95_low"))
        high = row.get("ci_high", row.get("ci95_high"))
        bound = y[i] == 0 and isinstance(high, (int, float)) and high > 0
        value = high if bound else y[i]
        plotted.append(value)
        if bound:
            ax.plot(x[i], value, "v", color="#087e8b", markerfacecolor="none")
        elif isinstance(low, (int, float)) and isinstance(high, (int, float)):
            ax.errorbar(x[i], value, yerr=[[max(0, value-low)], [max(0, high-value)]],
                        fmt="o", color="#087e8b", capsize=3)
        else:
            ax.plot(x[i], value, "o", color="#087e8b")
    if plotted and all(value > 0 for value in plotted):
        ax.set_yscale("log")
    ax.set(xlabel="Physical error probability p" if physical_axis else "Decoder prior probability p0 (explicit physical channel)" if prior_axis else "Circuit setting index",
           ylabel="Measured block / observable failure probability")
    adaptive = any(row.get("sampling_mode") == "adaptive_stopping" for row in rows)
    ax.set_title("Adaptive stopping: descriptive proportions; confidence intervals unavailable" if adaptive else "Measured results; open triangles show zero-failure interval upper limits", fontsize=9)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    print(output)

if __name__ == "__main__":
    main()
'''

PACKAGE_README = '''# Reproducible decoder experiment

This package runs locally with the shared implementations in
https://github.com/mertgkduman/survey_bp. The HTML interface does not run a
simulation. Results are created only when you execute the downloaded package.

## Install

```bash
git clone https://github.com/mertgkduman/survey_bp.git
cd survey_bp
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[performance,circuit,analysis]'
```

Use the same environment to run this package from any directory:

```bash
/path/to/survey_bp/.venv/bin/python run.py --repo /path/to/survey_bp --validate-only
OMP_NUM_THREADS=1 /path/to/survey_bp/.venv/bin/python run.py --repo /path/to/survey_bp --output ./results/run-001
/path/to/survey_bp/.venv/bin/python analyse.py ./results/run-001
```

All configuration is in `experiment.json`; `decoder.json` is a convenient copy
of its decoder section. The package manifest binds the exported bytes. To edit
an experiment, import its JSON in the interface (or use the terminal exporter),
validate it, and export a new package. A changed configuration has a new identity.

The run records the effective decoder settings, code/circuit identity, actual
implementation sources and environment, sampling procedure, event ledger, and
measured summaries. Existing output directories are rejected. Sampling and
iteration limits come from the specification; start with small counts when
checking a new configuration. Runtime includes the boundaries declared in the
summary; it is not an across-machine speed comparison.

Code-capacity logical failure includes syndrome-inconsistent outputs and
syndrome-consistent nontrivial logical residuals. Exact and stabilizer-equivalent
recoveries succeed. Circuit experiments instead evaluate observable prediction
errors; a detector fit alone is not a logical-success test. The circuit adapter
uses the independent-mechanism Stim detector error model and its explicit
historical numerical profile. Unsupported policies fail validation.

This exported experiment is a new canonical experiment unless its complete
identity is explicitly registered. A link to a paper or a parent specification
does not establish source-faithful reproduction. Refer to the catalog's original
configuration, summary, and analysis links for historical evidence.
'''

REGISTERED_RUN_SCRIPT = '''"""Execute the original registered study through ensure_study."""
from __future__ import annotations
import argparse
from hashlib import sha256, file_digest
import json
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="optional separate results root; default verifies/reuses retained repository results")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    for name, expected in json.loads((root / "package-manifest.json").read_text())["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Exported package content differs from its manifest")
    request = json.loads((root / "registered-experiment.json").read_text())
    repo = args.repo.expanduser().resolve()
    for name, expected in request["repository_inputs"].items():
        path = (repo / name).resolve()
        if not path.is_relative_to(repo) or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Original registered input changed or unavailable: {name}")
    if args.validate_only:
        print(json.dumps(request, indent=2))
        return
    sys.path.insert(0, str(repo / "src"))
    from bp_registry.study import ensure_study
    result = ensure_study(repo / request["study_path"], repo / request["decoder_path"],
                          results_root=args.output, workers=args.workers)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''

REGISTERED_README = '''# Original registered study workflow

Install the repository and dependencies as described in INSTALL.md. This package
uses the existing bp_registry.study.ensure_study API. It verifies and reuses the
registered results when available; if absent, that API executes the original
frozen campaign. Inspect registered-experiment.json and its budget note before
running. This is a compute-bearing command, not a browser simulation.

python run.py --repo /path/to/survey_bp --validate-only
python run.py --repo /path/to/survey_bp --workers 1

The optional --output argument selects a different results root. Existing
incomplete evidence is preserved and the registered API rejects incompatible
or partial caches. These study-specific settings are not the portable custom
experiment schema. Editing them requires a new study identity.
'''


IMPORT_RECEIPT = {"schema": "research-import-receipt-v1",
    "required_result_files": ["result-manifest.json", "run-manifest.json", "status.json", "requested-spec.json", "effective-spec.json", "events.jsonl", "summary.json", "summary.csv"],
    "browser_validation": {"require_result_manifest": True, "verify_all_bound_sha256": True, "recompute_ledger_summary_counts": True, "derive_catalog_from_bound_results": True, "uploaded_catalog_entry": "ignored; regenerated from bound evidence", "naked_catalog_entry": "reject"},
    "repository_persistence": {"command": "bp-registry-research import-results RESULT_DIRECTORY", "api": "bp_registry.research.results.persistent_import", "copies_raw_ledger": False}}


def package_template() -> dict[str, Any]:
    """Return precisely the text assets used by Python and browser exporters."""
    return {
        "schema": "research-package-template-v1",
        "files": {
            "run.py": RUN_SCRIPT,
            "analyse.py": ANALYSIS_SCRIPT,
            "import-receipt.json": json.dumps(IMPORT_RECEIPT, indent=2, sort_keys=True) + "\n",
            "README.md": PACKAGE_README,
            "requirements.txt": (
                "# First install survey_bp from its checkout, as described in README.md.\n"
                "numba==0.64.0\nstim==1.15.0\nsinter==1.15.0\nmatplotlib==3.10.9\n"
            ),
        },
        "registered_files": {"run.py": REGISTERED_RUN_SCRIPT, "README.md": REGISTERED_README,
                             "INSTALL.md": "# Installation\n\nClone https://github.com/mertgkduman/survey_bp, create a Python 3.12+ venv, and install the checkout with `python -m pip install -e '.[performance,circuit,analysis]'`. Use that environment for `python run.py --repo /path/to/survey_bp --validate-only`, followed by the command in README.md. The original registered result package supplies its summary, plots, and original analysis links.\n"},
    }


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def package_files(spec: dict[str, Any], *, repository: str | Path | None = None) -> dict[str, bytes]:
    """Validate a request and return a complete package, without executing it."""
    from .contracts import materialize_experiment, validate_experiment

    validate_experiment(spec, repository=repository)
    portable = materialize_experiment(spec, repository=repository)
    files = {name: text.encode() for name, text in package_template()["files"].items()}
    # Preserve the requested data, including explicit provenance. Runtime writes
    # its fully resolved settings separately and never infers a paper verdict.
    files["experiment.json"] = _json(portable)
    files["decoder.json"] = _json(portable.get("decoder", {}))
    problem = portable.get("problem", {})
    circuit = problem.get("circuit", {})
    if isinstance(circuit, dict) and isinstance(circuit.get("text"), str):
        files["inputs/circuit.stim"] = circuit["text"].encode()
    code = problem.get("code", {})
    if isinstance(code, dict) and code.get("kind") == "embedded_css":
        files["inputs/code.json"] = _json({name: value for name, value in code.items() if name != "kind"})
    if problem.get("kind") == "circuit":
        from .inputs import input_registry
        root = Path(repository).resolve() if repository is not None else Path(__file__).resolve().parents[3]
        for item in input_registry(root)["circuits"]:
            source = root / item["path"]
            if source.read_bytes() == circuit.get("text", "").encode():
                metadata = json.loads((root / item["manifest_path"]).read_text())
                files["inputs/circuit-source.json"] = _json({"circuit_id": item["circuit_id"],
                    "circuit_sha256": sha256(source.read_bytes()).hexdigest(),
                    **{key: metadata.get(key) for key in ("upstream_repository", "upstream_commit", "upstream_tag", "license")}})
                for name in item["license_paths"]:
                    files["inputs/" + Path(name).name] = (root / name).read_bytes()
                break
    files["import-receipt.json"] = _json(IMPORT_RECEIPT)
    files["package-manifest.json"] = _json({
        "schema": "research-package-manifest-v1",
        "files": {name: sha256(content).hexdigest() for name, content in sorted(files.items())},
    })
    return files


def export_package(spec: dict[str, Any], destination: str | Path, *,
                   repository: str | Path | None = None) -> Path:
    """Create a new ZIP. Existing files are preserved, including on validation errors."""
    files = package_files(spec, repository=repository)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, content in sorted(files.items()):
                item = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                item.external_attr = 0o644 << 16
                archive.writestr(item, content)
    return target


def registered_package_files(experiment_id: str, *, repository: str | Path) -> dict[str, bytes]:
    """Bundle an actual registered ensure_study workflow without running it."""
    from .catalog import build_catalog
    root = Path(repository).resolve()
    experiment = next((item for item in build_catalog(root)["experiments"]
                       if item["experiment_id"] == experiment_id), None)
    if experiment is None or experiment.get("reproduction_recipe", {}).get("kind") != "registered_study":
        raise ValueError("This experiment uses its source-specific runner; export a new supported experiment or inspect its original commands")
    recipe = experiment["reproduction_recipe"]
    files = {name: content.encode() for name, content in package_template()["registered_files"].items()}
    identities = {}
    for field, label in (("study_path", "original-study"), ("decoder_path", "original-decoder")):
        path = (root / recipe[field]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("registered input is unavailable within the repository")
        content = path.read_bytes()
        identities[recipe[field]] = sha256(content).hexdigest()
        files[label + path.suffix] = content
    files["registered-experiment.json"] = _json({"schema": "registered-study-package-v1",
        "experiment_id": experiment_id, **recipe, "repository_inputs": identities,
        "evidence_status": experiment["evidence_status"]})
    files["package-manifest.json"] = _json({"schema": "research-package-manifest-v1",
        "files": {name: sha256(content).hexdigest() for name, content in sorted(files.items())}})
    return files


def export_registered_package(experiment_id: str, destination: str | Path, *, repository: str | Path) -> Path:
    files = registered_package_files(experiment_id, repository=repository)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    return target
