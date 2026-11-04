"""Shared evidence boundaries for portable result producers and importers."""

def timing_boundaries(kind: str) -> dict:
    return {"decode_seconds": "per retained shot: Sinter prediction call only; excludes detector-prefix sampling, detailed audit decode, observable comparison, and file I/O" if kind == "circuit" else "one decoder call (both X/Z component calls for binary), excluding graph construction and sampling",
                "end_to_end_seconds": "per retained shot: Sinter prediction + detailed canonical audit decode + observable comparison and event construction; excludes parse/DEM/setup, bounded-prefix sampling, and file I/O" if kind == "circuit" else "per shot: sampling + decoder + independent recovery evaluation; excludes graph/code setup, file I/O, and run provenance hashing",
                "audit_second_decode": kind == "circuit"}
