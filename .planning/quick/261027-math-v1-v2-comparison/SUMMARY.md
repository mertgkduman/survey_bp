---
status: complete
date: 2026-10-27
---

# Compact v1/v2 equation comparison

Replaced the generated HTML and PDF with a concise comparison of binary SPA
and four-state BP4. Each family has v1 and v2 side by side. All displayed
equations are rendered as vector math with STIX glyphs; the HTML embeds its
SVG equations and requires no external script or network connection. The PDF
has two pages, one per kernel family.

The comparison records v1 clipping and ordered box-plus, v2 tanh-product
checks, unclipped finite beliefs, V2C damping, and the BP4 decision and
stopping differences. No decoder implementation or historical evidence was
changed.

Verification: generated both files without math-renderer warnings; opened
and visually inspected the HTML in headless Firefox; rendered and inspected
the PDF page layout using the same Matplotlib figure; checked text for
overflow and overlap. Parsed all 19 embedded SVG equations, confirmed two
HTML sections and two PDF pages, checked profile constants against the
current code, and passed `git diff --check`.
