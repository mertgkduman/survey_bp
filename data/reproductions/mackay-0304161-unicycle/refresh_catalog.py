"""Refresh the workbench without overwriting a concurrently edited catalog."""

import json
import os
import subprocess

from bp_registry.research.catalog import build_catalog
from run import REPO, RESULTS


if __name__ == "__main__":
    destination = REPO / "web/research/catalog.json"
    original = destination.read_bytes()
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(destination)], cwd=REPO).returncode == 0
    catalog = build_catalog(REPO)
    # CLI build generates matrix assets, while this summary refresh preserves them.
    previews = {row["code_id"]: row["matrix_asset"] for row in json.loads(original)["codes"] if "matrix_asset" in row}
    for row in catalog["codes"]:
        if row["code_id"] in previews:
            row["matrix_asset"] = previews[row["code_id"]]
    data = (json.dumps(catalog, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (RESULTS / "catalog.json").write_bytes(data)
    if clean and destination.read_bytes() == original:
        temporary = destination.with_suffix(".unicycle.tmp")
        temporary.write_bytes(data)
        os.replace(temporary, destination)
        print(f"Updated {destination}")
    else:
        print(f"Workbench has local edits; refreshed catalog saved to {RESULTS / 'catalog.json'}")
