"""Write a deterministic fixed-shot, paired campaign from the TeX points."""

from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_SOURCE_FAILURES = 125
SHARD_SIZE = 10_000
IMPLEMENTATION_FILES = (
    "data/reproductions/yao-2312-10950-vanilla/run.py",
    "data/reproductions/yao-2312-10950-vanilla/run_task.py",
    "data/reproductions/yao-2312-10950-vanilla/codes/a5.json",
    "data/reproductions/yao-2312-10950-vanilla/codes/b2.json",
    *(f"data/reproductions/yao-2312-10950-vanilla/decoders/{name}.json"
      for name in ("bp4_v1", "bp4_v2", "binary_v1", "binary_v2")),
    "src/bp_registry/code_constructions.py",
    "src/bp_registry/css.py",
    "src/bp_registry/canonical/compiled.py",
    "src/bp_registry/canonical/numerics.py",
    "src/bp_registry/quaternary/compiled.py",
    "src/bp_registry/quaternary/numerics.py",
    "src/bp_registry/quaternary/problems.py",
)


def plan() -> dict[str, object]:
    source_bytes = (ROOT / "source_points.json").read_bytes()
    source = json.loads(source_bytes)
    points = []
    tasks = []
    index = 0
    for p in reversed(tuple(float(key) for key in source["curves"]["a5"]["p_to_qbp_rate"])):
        key = f"{p:.2f}"
        for code in ("a5", "b2"):
            rate = source["curves"][code]["p_to_qbp_rate"][key]
            shots = math.ceil(EXPECTED_SOURCE_FAILURES / rate)
            seed = 231210950 + (0 if code == "a5" else 100) + round(p * 100)
            point = {"code": code, "p": p, "source_qbp_rate": rate,
                     "planned_shots": shots, "seed": seed,
                     "expected_source_failures": shots * rate}
            points.append(point)
            for start in range(0, shots, SHARD_SIZE):
                task = {"index": index, "code": code, "p": p, "seed": seed,
                        "start_shot": start, "shots": min(SHARD_SIZE, shots-start),
                        "output": f"results/shards/{code}_p{round(p*100):02d}_{start:07d}"}
                tasks.append(task)
                index += 1
    return {
        "schema": "yao-vanilla-campaign-plan-v1",
        "source_points_sha256": sha256(source_bytes).hexdigest(),
        "implementation_files_sha256": {
            name: sha256((REPO / name).read_bytes()).hexdigest() for name in IMPLEMENTATION_FILES
        },
        "design": "fixed paired N chosen before local results; ceil(125 / published Q-BP point estimate)",
        "expected_source_failures_per_point": EXPECTED_SOURCE_FAILURES,
        "shard_size": SHARD_SIZE,
        "points": points,
        "tasks": tasks,
    }


def main() -> None:
    destination = ROOT / "campaign.json"
    if destination.exists():
        raise FileExistsError("campaign.json exists; do not silently alter a launched campaign")
    payload = plan()
    destination.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(f"{len(payload['points'])} points, {len(payload['tasks'])} shards, "
          f"{sum(point['planned_shots'] for point in payload['points'])} paired shots")


if __name__ == "__main__":
    main()
