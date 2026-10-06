#!/usr/bin/env python3
"""Fail-closed qualification for the approved Phase 7 standalone OSD source.

The script never installs into the project's interpreter.  It creates a fresh
isolated virtual environment, checks out only the approved source commit, then
records either an admitted receipt or every failed gate in the committed JSON
receipt.  A failed receipt is intentionally non-runnable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


REPOSITORY = "https://github.com/quantumgizmos/ldpc.git"
COMMIT = "baec4c8bfa2a679b0ba0e72df5582e277cd6918b"
BUILD_REQUIREMENTS = (
    "setuptools>=68.2.2", "Cython>=3.0.2", "numpy", "scipy", "tqdm", "pytest", "stim",
    "sinter>=1.12.0", "pymatching",
)


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _receipt_digest(receipt: dict[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_sha256", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _primary_ldpc_version(python: Path) -> str:
    return _run([str(python), "-c", "import ldpc; print(ldpc.__version__) "]).stdout.strip()


def _probe_api(python: Path) -> dict[str, Any]:
    probe = r'''
import json
import numpy as np
from ldpc.osd_decoder import OsdDecoder

fixtures = {
    "full_rank": (np.asarray([[1, 0, 0], [0, 1, 0]], dtype=np.uint8), np.asarray([1, 0], dtype=np.uint8), np.asarray([.1, .2, .3])),
    "rank_deficient": (np.asarray([[1, 1, 0], [1, 1, 0]], dtype=np.uint8), np.asarray([1, 1], dtype=np.uint8), np.asarray([.1, .2, .3])),
    "equal_weight": (np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8), np.asarray([1, 0], dtype=np.uint8), np.asarray([1., 1., 1.])),
}
methods = (("OSD_0", 0), ("OSD_E", 2), ("OSD_CS", 2))
observed = []
for fixture_name, (matrix, syndrome, weights) in fixtures.items():
    for method, order in methods:
        decoder = OsdDecoder(matrix, osd_method=method, osd_order=order,
                             channel_probabilities=np.full(matrix.shape[1], .1))
        candidate = np.asarray(decoder.decode(syndrome, weights), dtype=np.uint8)
        observed.append({
            "fixture": fixture_name,
            "method": method,
            "order": order,
            "candidate": candidate.tolist(),
            "syndrome_valid": bool(np.array_equal((matrix @ candidate) % 2, syndrome)),
            "osd0_candidate": np.asarray(decoder.osd0_decoding, dtype=np.uint8).tolist(),
            "final_candidate": np.asarray(decoder.osdw_decoding, dtype=np.uint8).tolist(),
        })
decoder = OsdDecoder(fixtures["full_rank"][0], osd_method="OSD_0", osd_order=0,
                     channel_probabilities=np.full(3, .1))
print(json.dumps({
    "module": "ldpc.osd_decoder",
    "class": "OsdDecoder",
    "methods": ["OSD_0", "OSD_E", "OSD_CS"],
    "decode_surface": "decode(syndrome, bit_weights)",
    "properties": ["osd_method", "osd_order", "osd0_decoding", "osdw_decoding"],
    "candidate_enumeration_exposed": hasattr(decoder, "osd_candidate_strings"),
    "fixtures": observed,
}, sort_keys=True))
'''
    return json.loads(_run([str(python), "-c", probe]).stdout)


def qualify(*, receipt_path: Path, work_root: Path | None) -> int:
    primary_python = Path(sys.executable)
    before = _primary_ldpc_version(primary_python)
    root = work_root or Path(tempfile.mkdtemp(prefix="phase7-standalone-osd-"))
    source = root / "source"
    venv = root / "venv"
    wheel_dir = root / "wheel"
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "qualification": "phase7_standalone_osd",
        "disposition": "failed",
        "runnable": False,
        "source": {"repository": REPOSITORY, "commit": COMMIT},
        "primary_environment": {"python": str(primary_python), "ldpc_version_before": before},
        "build": {"work_root": str(root), "build_requirements": list(BUILD_REQUIREMENTS)},
        "api": {},
        "fixtures": {},
        "failure_reasons": [],
    }
    try:
        if not source.exists():
            _run(["git", "clone", "--no-checkout", REPOSITORY, str(source)])
        _run(["git", "checkout", "--detach", COMMIT], cwd=source)
        checked_out = _run(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
        if checked_out != COMMIT:
            raise RuntimeError("checked_out_commit_mismatch")
        archive = subprocess.run(
            ["git", "archive", "--format=tar", COMMIT], cwd=source,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout
        receipt["source"].update({"checked_out_commit": checked_out, "tree_sha256": hashlib.sha256(archive).hexdigest()})
        if not venv.exists():
            _run([str(primary_python), "-m", "venv", str(venv)])
        isolated_python = venv / "bin/python"
        _run([str(isolated_python), "-m", "pip", "install", *BUILD_REQUIREMENTS])
        wheels = tuple(sorted(wheel_dir.glob("ldpc-*.whl")))
        if not wheels:
            _run([str(isolated_python), "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--wheel-dir", str(wheel_dir), str(source)])
            wheels = tuple(sorted(wheel_dir.glob("ldpc-*.whl")))
        if len(wheels) != 1:
            raise RuntimeError("expected_exactly_one_ldpc_wheel")
        wheel = wheels[0]
        _run([str(isolated_python), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheel)])
        freeze = _run([str(isolated_python), "-m", "pip", "freeze"]).stdout
        receipt["build"].update({
            "qualified_python": str(isolated_python),
            "wheel_filename": wheel.name,
            "wheel_sha256": _sha256(wheel),
            "dependency_freeze_sha256": hashlib.sha256(freeze.encode("utf-8")).hexdigest(),
            "dependency_freeze": freeze.splitlines(),
            "compiler": _run(["c++", "--version"]).stdout.splitlines()[0],
        })
        api = _probe_api(isolated_python)
        receipt["api"] = {key: value for key, value in api.items() if key != "fixtures"}
        fixture_results = api["fixtures"]
        receipt["fixtures"] = {
            "results": fixture_results,
            "all_syndrome_valid": all(item["syndrome_valid"] for item in fixture_results),
        }
        if not receipt["fixtures"]["all_syndrome_valid"]:
            receipt["failure_reasons"].append("tiny_matrix_syndrome_validation_failed")
        if not api["candidate_enumeration_exposed"]:
            receipt["failure_reasons"].append("required_higher_order_candidate_enumeration_not_exposed")
        receipt["primary_environment"]["ldpc_version_after"] = _primary_ldpc_version(primary_python)
        if receipt["primary_environment"]["ldpc_version_after"] != before:
            receipt["failure_reasons"].append("primary_environment_mutated")
        if not receipt["failure_reasons"]:
            receipt["disposition"] = "passed"
            receipt["runnable"] = True
    except Exception as error:
        receipt["failure_reasons"].append(f"qualification_exception:{type(error).__name__}:{error}")
        receipt["primary_environment"]["ldpc_version_after"] = _primary_ldpc_version(primary_python)
    _write_receipt(receipt_path, receipt)
    return 0 if receipt["disposition"] == "passed" else 2


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=root / "data/qualifications/phase7-standalone-osd-baec4c8.json")
    parser.add_argument("--work-root", type=Path, help="Fresh disposable directory; it is never placed in the repository.")
    args = parser.parse_args()
    return qualify(receipt_path=args.receipt.resolve(), work_root=args.work_root.resolve() if args.work_root else None)


if __name__ == "__main__":
    raise SystemExit(main())
