"""Import a pinned BeamSearch source checkout's tracked Stim circuits."""

from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile


UPSTREAM_COMMIT = "084a475b05fb64308103317a1ce5a0c4b0be58aa"
REPRESENTATIVE = "StimCircuit/BB[[144,12,12]],memory_Z,error_rate=0.005,syndrome_rounds=12.stim"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    if commit != UPSTREAM_COMMIT:
        raise ValueError(f"expected BeamSearch source commit {UPSTREAM_COMMIT}, got {commit}")
    paths = sorted(subprocess.check_output(
        ["git", "-C", str(args.source), "ls-files", "*.stim"], text=True,
    ).splitlines())
    if len(paths) != 38 or any(not path.startswith("StimCircuit/") for path in paths):
        raise ValueError("unexpected BeamSearch circuit inventory")
    args.destination.mkdir(parents=True, exist_ok=True)
    archive = args.destination / "beamsearch-circuits.tar.gz"
    records = []
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as tar:
                for path in paths:
                    payload = (args.source / path).read_bytes()
                    info = tarfile.TarInfo(path)
                    info.size = len(payload)
                    info.mode = 0o644
                    info.mtime = 0
                    tar.addfile(info, io.BytesIO(payload))
                    records.append({"path": path, "sha256": sha256(payload).hexdigest(), "bytes": len(payload)})
                    if path == REPRESENTATIVE:
                        (args.destination / "bb144-memory-z-p005.stim").write_bytes(payload)
    for name in ("LICENSE", "THIRDPARTY-LICENSES"):
        (args.destination / name).write_bytes((args.source / name).read_bytes())
    manifest = {
        "schema": "beamsearch_circuit_archive_v1",
        "upstream_repository": "https://github.com/ionq-publications/BeamSearchDecoder",
        "upstream_commit": commit,
        "archive": archive.name,
        "archive_sha256": sha256(archive.read_bytes()).hexdigest(),
        "license_sha256": sha256((args.destination / "LICENSE").read_bytes()).hexdigest(),
        "thirdparty_license_sha256": sha256((args.destination / "THIRDPARTY-LICENSES").read_bytes()).hexdigest(),
        "circuits": records,
        "representative": {"path": REPRESENTATIVE, "local_name": "bb144-memory-z-p005.stim"},
    }
    (args.destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Imported {len(paths)} circuits to {args.destination}")


if __name__ == "__main__":
    main()
