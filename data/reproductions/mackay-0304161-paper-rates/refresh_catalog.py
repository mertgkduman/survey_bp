"""Use the established concurrent-edit-safe static catalog refresh."""

from pathlib import Path

from run import ORIGINAL, REPO, RESULTS

if __name__ == "__main__":
    source = ORIGINAL / "refresh_catalog.py"
    exec(compile(source.read_bytes(), str(source), "exec"), {"__name__": "__main__"})
