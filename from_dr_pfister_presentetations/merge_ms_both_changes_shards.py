"""Merge deterministic B1 p=.14 hybrid MS shards into one audited point."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parent / "results/ms_both_changes_curve"
OUTPUT = ROOT / "b1_p0140"


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    shards = [ROOT / "shards" / f"b1_p0140_shard{index}" for index in range(5)]
    template = None
    counts = {"shots": 0, "type_i": 0, "type_ii": 0,
              "exact_success": 0, "stabilizer_success": 0,
              "total_iterations": 0}
    OUTPUT.mkdir(parents=True)
    digest = hashlib.sha256()
    with gzip.open(OUTPUT / "events.jsonl.gz", "wb", compresslevel=1) as merged:
        for index, folder in enumerate(shards):
            summary = json.loads((folder / "summary.json").read_text())
            if summary["code"] != "b1" or summary["physical_p"] != .14 or summary["seed"] != 20261215:
                raise ValueError(f"wrong shard identity: {folder}")
            if summary["start_shot"] != 2000 * index or summary["end_shot_exclusive"] != 2000 * (index + 1):
                raise ValueError(f"wrong shard range: {folder}")
            if template is None:
                template = summary.copy()
            else:
                for key in ("schema", "decoder_p0", "sampler", "max_iterations",
                            "q8_scalar_scale", "v2c_format", "projection",
                            "check_rule", "damping", "source_ler", "source_point_type"):
                    if summary[key] != template[key]:
                        raise ValueError(f"inconsistent shard field {key}: {folder}")
            shard_digest = hashlib.sha256()
            records = 0
            with gzip.open(folder / "events.jsonl.gz", "rb") as source:
                for raw in source:
                    record = json.loads(raw)
                    if record["shot"] != 2000 * index + records:
                        raise ValueError(f"noncontiguous shot sequence: {folder}")
                    records += 1
                    shard_digest.update(raw)
                    digest.update(raw)
                    merged.write(raw)
            if records != summary["counts"]["shots"] or shard_digest.hexdigest() != summary["event_ledger_uncompressed_sha256"]:
                raise ValueError(f"shard count or digest mismatch: {folder}")
            for key in counts:
                counts[key] += summary["counts"][key]
    if counts["shots"] != 10_000:
        raise ValueError("merged denominator is not 10,000")
    failures = counts["type_i"] + counts["type_ii"]
    ci = binomtest(failures, counts["shots"]).proportion_ci(.95, method="exact")
    result = {key: template[key] for key in
              ("schema", "code", "physical_p", "decoder_p0", "seed", "sampler",
               "max_iterations", "q8_scalar_scale", "v2c_format", "projection",
               "check_rule", "damping", "source_ler", "source_point_type")}
    result.update({
        "start_shot": 0, "end_shot_exclusive": 10_000,
        "shards": [str(folder.relative_to(ROOT)) for folder in shards],
        "counts": counts, "failures": failures,
        "ler": failures / counts["shots"],
        "lower_95": float(ci.low), "upper_95": float(ci.high),
        "upper_95_one_sided_if_zero": (float(1 - .05 ** (1 / counts["shots"]))
                                       if failures == 0 else None),
        "mean_iterations": counts["total_iterations"] / counts["shots"],
        "elapsed_seconds": sum(json.loads((folder / "summary.json").read_text())["elapsed_seconds"] for folder in shards),
        "event_ledger": "events.jsonl.gz",
        "event_ledger_uncompressed_sha256": digest.hexdigest(),
    })
    with (OUTPUT / "summary.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
