---
quick_id: 261119-jgk
status: complete
---

# Construction U table cell overflow

The block-error table uses fixed column widths and clips long values with ellipses. Each cell exposes its full text through a browser hover tooltip. The table follows its own horizontal scroll on narrow screens.

Chromium checks passed with one paper on desktop, two papers side by side, and the mobile layout. They verified clipping, adjacent column boundaries, and full hover text. The existing paper browser test now checks the table layout and tooltip attributes.
