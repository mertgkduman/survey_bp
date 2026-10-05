"""Researcher-facing study command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .study import ensure_study


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path, help="study JSON with code, noise, samples, and budgets")
    parser.add_argument("--decoder", required=True, type=Path, help="decoder policy TOML or JSON")
    parser.add_argument("--results-root", type=Path, help="directory for verified results")
    parser.add_argument("--workers", type=int, default=1, help="shot workers for registered campaigns")
    args = parser.parse_args(argv)
    result = ensure_study(args.study, args.decoder, results_root=args.results_root, workers=args.workers)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
