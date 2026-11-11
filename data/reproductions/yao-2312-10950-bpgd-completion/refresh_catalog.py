"""Build a local catalog from verified points and publish it to the preview."""

from hashlib import sha256
import json
import os
import subprocess

from bp_registry.research.catalog import build_catalog
from run import REPO, RESULTS


if __name__ == "__main__":
    destination = REPO / "web/research/catalog.json"
    snapshot = RESULTS / "catalog.json"
    was_clean = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", str(destination)],
        check=False,
    ).returncode == 0
    original = destination.read_bytes()
    previews = {code["code_id"]: code["matrix_asset"] for code in json.loads(original)["codes"]
                if "matrix_asset" in code}
    catalog = build_catalog(REPO)
    for code in catalog["codes"]:
        if code["code_id"] in previews:
            code["matrix_asset"] = previews[code["code_id"]]
    snapshot.write_text(json.dumps(catalog, indent=2, sort_keys=True, allow_nan=False) + "\n")
    if was_clean and sha256(original).digest() == sha256(destination.read_bytes()).digest():
        temporary = destination.with_suffix(".completion.tmp")
        temporary.write_bytes(snapshot.read_bytes())
        os.replace(temporary, destination)
        print(f"Updated {destination}")
    else:
        print(f"Catalog has local edits. Refreshed copy saved to {snapshot}")
