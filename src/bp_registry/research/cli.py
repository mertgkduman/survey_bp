"""Browse evidence, export experiments, and preview the research interface."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
from typing import Any
from urllib.parse import unquote, urlsplit


def repository_root(requested: str | Path | None = None) -> Path:
    root = Path(requested).expanduser().resolve() if requested else Path(__file__).resolve().parents[3]
    if not (root / "pyproject.toml").is_file() or not (root / "src/bp_registry").is_dir():
        raise ValueError("Supply --repo with the survey_bp checkout location")
    return root


def read_spec(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Experiment input must be a JSON object")
    return value


def build_interface(repository: str | Path | None = None) -> dict[str, Any]:
    from .catalog import build_catalog
    from .contracts import interface_contract
    from .export import package_template

    root = repository_root(repository)
    destination = root / "web/research"
    destination.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog(root)
    for filename, data in (
        ("catalog.json", catalog),
        ("contract.json", interface_contract()),
        ("package-template.json", package_template()),
    ):
        (destination / filename).write_text(
            json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return {"status": "built", "directory": str(destination),
            "papers": len(catalog.get("papers", [])),
            "experiments": len(catalog.get("experiments", [])),
            "datasets": len(catalog.get("datasets", []))}


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serve the static workbench and tracked evidence, without directory listings."""

    def __init__(self, *args: Any, root: Path, allowed: frozenset[str], **kwargs: Any):
        self.root = root
        self.allowed = allowed
        super().__init__(*args, directory=str(root), **kwargs)

    def send_head(self):
        request = unquote(urlsplit(self.path).path)
        if request == "/":
            self.send_response(302)
            self.send_header("Location", "/web/research/")
            self.end_headers()
            return None
        parts = Path(request.lstrip("/")).parts
        if any(part.startswith(".") for part in parts):
            self.send_error(403, "This preview serves interface and registered repository files")
            return None
        candidate = (self.root / request.lstrip("/")).resolve()
        if not candidate.is_relative_to(self.root):
            self.send_error(403)
            return None
        if candidate.is_dir() and candidate == self.root / "web/research":
            candidate = candidate / "index.html"
        relative = candidate.relative_to(self.root).as_posix()
        if not (relative in self.allowed or relative.startswith("web/research/")):
            self.send_error(404, "File is not part of the published repository/interface")
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(403, "Directory listings are disabled")
        return None


def preview_server(repository: str | Path | None = None, *, port: int = 8765,
                   host: str = "127.0.0.1") -> ThreadingHTTPServer:
    root = repository_root(repository)
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True,
    ).stdout.decode().split("\0")
    allowed = frozenset(path for path in tracked if path and not any(
        part.startswith(".") for part in Path(path).parts))
    return ThreadingHTTPServer((host, port), partial(PreviewHandler, root=root, allowed=allowed))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="survey_bp checkout; defaults to this installation")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("build", help="regenerate static catalog and shared contracts")
    serve = actions.add_parser("serve", help="serve the repository-hostable research interface")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--no-build", action="store_true", help="use the checked-in static catalog")
    listing = actions.add_parser("list", help="list registered catalog entities")
    listing.add_argument("entity", choices=("papers", "decoders", "codes", "circuits", "experiments", "datasets"))
    validate = actions.add_parser("validate", help="validate an experiment without sampling")
    validate.add_argument("spec", type=Path)
    export = actions.add_parser("export", help="create a portable new experiment ZIP")
    export.add_argument("spec", type=Path)
    export.add_argument("--output", type=Path, required=True)
    registered = actions.add_parser("export-registered", help="package an original registered ensure_study workflow")
    registered.add_argument("experiment_id")
    registered.add_argument("--output", type=Path, required=True)
    run = actions.add_parser("run", help="execute a validated experiment into a new directory")
    run.add_argument("spec", type=Path)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.repo)
        if args.action == "build":
            result = build_interface(root)
        elif args.action == "serve":
            if not args.no_build:
                build_interface(root)
            server = preview_server(root, port=args.port, host=args.host)
            print(f"Research interface: http://{args.host}:{server.server_port}/web/research/", flush=True)
            print("Browsing and downloads run in the browser. New simulations run locally after download.", flush=True)
            try:
                server.serve_forever(poll_interval=.25)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return
        elif args.action == "list":
            from .catalog import build_catalog
            result = build_catalog(root)[args.entity]
        elif args.action == "validate":
            from .contracts import validate_experiment
            result = validate_experiment(read_spec(args.spec), repository=root)
        elif args.action == "export":
            from .export import export_package
            target = export_package(read_spec(args.spec), args.output, repository=root)
            result = {"status": "exported", "path": str(target)}
        elif args.action == "export-registered":
            from .export import export_registered_package
            target = export_registered_package(args.experiment_id, args.output, repository=root)
            result = {"status": "exported_registered_workflow", "path": str(target)}
        else:
            from .runner import run_experiment
            result = run_experiment(read_spec(args.spec), output=args.output, repository=root)
        print(json.dumps(result, indent=2, sort_keys=True, default=str, allow_nan=False))
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
