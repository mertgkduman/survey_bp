"""Import the pinned Relay-BP circuit fixtures without changing their bytes."""

from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile


UPSTREAM_COMMIT = "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
REPRESENTATIVES = {
    "bicycle_bivariate_18_4_3_memory_X": "bicycle_bivariate/circuit=bicycle_bivariate_18_4_3_memory_X,distance=3,rounds=3,error_rate=0.005,noise_model=uniform_circuit,basis=CX,A=x+1+y,B=x+1+xy^2.stim",
    "bicycle_bivariate_144_12_12_memory_Z": "bicycle_bivariate/circuit=bicycle_bivariate_144_12_12_memory_Z,distance=12,rounds=12,error_rate=0.005,noise_model=uniform_circuit,basis=CX,A=x^3+y+y^2,B=y^3+x+x^2.stim",
    "superdense_color_code_memory_Z": "color/circuit=superdense_color_code_memory_Z,distance=3,rounds=3,error_rate=0.005,noise_model=uniform_circuit,basis=CX.stim",
    "rotated_surface_code_memory_X": "surface/circuit=rotated_surface_code_memory_X,distance=3,rounds=3,error_rate=0.005,noise_model=uniform_circuit,basis=CX.stim",
}


def import_circuits(source: Path, destination: Path) -> dict[str, object]:
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if commit != UPSTREAM_COMMIT:
        raise ValueError(f"expected Relay v0.2.2 commit {UPSTREAM_COMMIT}, got {commit}")
    paths = subprocess.check_output(["git", "-C", str(source), "ls-files", "*.stim"], text=True).splitlines()
    paths = sorted(path for path in paths if path.startswith("tests/testdata/"))
    if len(paths) != 672:
        raise ValueError(f"expected 672 tracked Relay circuit fixtures, got {len(paths)}")
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    archive = destination / "relay-circuits.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for path in paths:
                    payload = (source / path).read_bytes()
                    relative = path.removeprefix("tests/testdata/")
                    info = tarfile.TarInfo(relative)
                    info.size = len(payload)
                    info.mode = 0o644
                    info.mtime = 0
                    tar.addfile(info, io.BytesIO(payload))
                    entries.append({"path": relative, "sha256": sha256(payload).hexdigest(), "bytes": len(payload)})
                    for name, selected in REPRESENTATIVES.items():
                        if relative == selected:
                            (destination / f"{name}.stim").write_bytes(payload)
    license_bytes = (source / "LICENSE.txt").read_bytes()
    (destination / "LICENSE.txt").write_bytes(license_bytes)
    manifest: dict[str, object] = {
        "schema": "relay_circuit_archive_v1",
        "upstream_repository": "https://github.com/trmue/relay",
        "upstream_tag": "v0.2.2",
        "upstream_commit": commit,
        "license": "Apache-2.0",
        "license_sha256": sha256(license_bytes).hexdigest(),
        "archive": archive.name,
        "archive_sha256": sha256(archive.read_bytes()).hexdigest(),
        "circuits": entries,
        "representatives": REPRESENTATIVES,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="checkout of the exact Relay v0.2.2 commit")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = import_circuits(args.source, args.destination)
    print(f"Imported {len(result['circuits'])} circuits to {args.destination}")
