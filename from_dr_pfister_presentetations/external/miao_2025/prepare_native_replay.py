"""Export the exact Python pilot shots for the pinned Miao C++ decoder."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from run_reproduction import sample_error


TO_SOURCE = np.asarray((0, 1, 3, 2), dtype=np.uint8)  # local I,X,Y,Z -> source I,X,Z,Y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    if summary["code"] != "miao_toric_d4":
        raise ValueError("native replay export requires the pinned Miao toric code")
    path = args.summary.parent / "native_input.txt"
    if path.exists():
        raise FileExistsError(path)
    ledger = args.summary.parent / summary["event_ledger"]
    first_arm = summary["configs"][0]["id"]
    expected = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["arm"] == first_arm:
            expected[record["shot"]] = record["error_sha256"]
    if len(expected) != summary["shots"]:
        raise ValueError("pilot ledger does not contain one first-arm event per shot")
    rng = np.random.Generator(np.random.PCG64(summary["seed"]))
    with path.open("w", encoding="utf-8") as handle:
        for shot in range(summary["shots"]):
            error = sample_error(rng, 32, summary["physical_p"])
            if hashlib.sha256(error.tobytes()).hexdigest() != expected[shot]:
                raise ValueError(f"native replay input differs from pilot shot {shot}")
            handle.write(" ".join(map(str, TO_SOURCE[error].tolist())) + "\n")
    manifest = {"source_pilot_summary": args.summary.name, "shots": summary["shots"],
                "seed": summary["seed"], "physical_p": summary["physical_p"],
                "source_pauli_order": "I=0,X=1,Z=2,Y=3", "input": path.name,
                "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (args.summary.parent / "native_input_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
