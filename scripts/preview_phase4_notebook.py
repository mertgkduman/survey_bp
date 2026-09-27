"""Save a portable local preview of the executed Phase 4 notebook outputs."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re

import nbformat

from phase4_notebook_support import confined


def _markdown(source: str) -> str:
    # Preview prose stays escaped. Rich tables/figures are retained from outputs.
    blocks = []
    for paragraph in source.split("\n\n"):
        heading = re.fullmatch(r"(#{1,6}) ([^\n]+)", paragraph)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{escape(heading.group(2))}</h{level}>")
        else:
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(paragraph))
            blocks.append("<p>" + text.replace("\n", "<br>") + "</p>")
    return "\n".join(blocks)


def preview_notebook(root: Path, source: str, destination: str, *, section: str | None = None) -> Path:
    source_path = confined(root, source, "data/results/phase4-notebook")
    output_path = confined(root, destination, "data/results/phase4-notebook")
    if source_path == output_path or output_path.suffix != ".html":
        raise ValueError("preview must be a separate HTML artifact")
    notebook = nbformat.read(source_path, as_version=4)
    if section is not None and section not in {cell.metadata.get("phase4_section") for cell in notebook.cells}:
        raise ValueError("preview section is absent from the notebook")
    mode = notebook.metadata.get("phase4_validation", {}).get("mode", "unrecorded")
    cells = []
    for cell in notebook.cells:
        if section is not None and cell.metadata.get("phase4_section") != section:
            continue
        if cell.cell_type == "markdown":
            stage = cell.metadata.get("phase4_section")
            prose = _markdown(cell.source)
            cells.append(f'<section id="{escape(str(stage), quote=True)}">{prose}</section>' if stage else prose)
        elif cell.cell_type == "code":
            cells.append("<details><summary>Executed code</summary><pre>" + escape(cell.source) + "</pre></details>")
            for output in cell.get("outputs", []):
                data = output.get("data", {})
                if "image/png" in data:
                    encoded = "".join(data["image/png"].split())
                    cells.append(f'<img alt="Retained notebook figure" src="data:image/png;base64,{encoded}">')
                elif "text/html" in data:
                    cells.append(data["text/html"])
                elif "text/plain" in data:
                    cells.append("<pre>" + escape(data["text/plain"]) + "</pre>")
                elif output.get("output_type") == "stream":
                    cells.append("<pre>" + escape(output.get("text", "")) + "</pre>")
                elif output.get("output_type") == "error":
                    raise ValueError("preview requires an executed notebook without cell errors")
    html = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phase 4 notebook preview</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#202832;background:#f4f6f8;margin:0}
main{max-width:1050px;margin:24px auto;padding:28px;background:white;border-radius:8px}
h1,h2,h3,h4{line-height:1.25} h2{margin-top:2em;border-top:1px solid #d8dde3;padding-top:1em}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 monospace;background:#f4f6f8;padding:12px}
img{display:block;width:100%;height:auto;margin:20px auto}td,th{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #d8dde3}
th{background:#eef2f6}details{margin:12px 0}summary{cursor:pointer;color:#345c82}
@media(max-width:700px){main{margin:0;padding:16px;border-radius:0}body{font-size:15px}}
</style><main><h1>Phase 4 executed notebook</h1>"""
    html += f"<p>Mode: <strong>{escape(str(mode))}</strong>. Assessment: not_assessed.</p>"
    if section is not None:
        html += f"<p>Selected section: {escape(section)}.</p>"
    html += "\n".join(cells) + "</main></html>"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--section", help="Preview one retained research section")
    args = parser.parse_args()
    print(preview_notebook(Path(__file__).resolve().parents[1], args.input, args.output, section=args.section))


if __name__ == "__main__":
    main()
