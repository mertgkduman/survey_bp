# Roffe BP-OSD source comparison

This is a source-data table/report for the four Figure3 toric codes in the current study. It does not run BP-OSD or alter the active measured catalog. See RESULTS.md for all108 plotted BP+OSD-CS values,109 source-rate rows, all four local confirmation arms, explicit missing source values, and separate source threshold context.

Rebuild from the exact original arXiv v2 source archive:

```sh
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-osd-comparison/compare.py --archive /path/to/source.tar
```

The default archive is the existing .git/roffe-source/source.tar cache. Download source via https://arxiv.org/src/2005.07016v2 if needed; the extractor checks archive and vector-member SHA256 before use. source_points.json retains all extracted numerical geometry, evidence hashes and unknown author quantities for inspection without the cache.

Paper values are approximate. The extractor uses main-panel coordinate calibration, maps line color to code distance, distinguishes dashed BP from solid BP+OSD-CS, excludes the zoom inset, checks exact25/28/28/27 BP-OSD inventories and matches every vertex to its drawn vertical error bar. It independently reproduces all109 frozen dashed-BP vertices. The missing length450/p=.01 BP-OSD point stays unavailable. Drawn source error-bar geometry is not called a95% interval because its confidence convention is not supplied.

Source BP+OSD-CS uses X-only noise, BP capT=n and search-depth lambda60. Local binary BP shares that channel. Q-BP is depolarizing at1.5p and remains different-channel context. OSD adds matrix elimination/search work; author mean iterations, total work and raw sample counts are unavailable. No equal-total-work claim, inferred missing point or pooled source/confirmation estimate is produced. Original frozen studies, kernels, manifests and raw evidence remain unchanged.
