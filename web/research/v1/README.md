# Research interface v1 (archived)

This preserves the static interface shipped in commit `a629772`.
Open `/web/research/v1/` through the local preview server. The current v2 interface
is `/web/research/`.

The original HTML, JavaScript, CSS, ZIP writer, catalog, contract, and package
template are retained. The HTML adds an archive label/backlink, and JavaScript
repository asset URLs traverse one extra directory. Original source data and
frozen decoder identities have not moved. Catalog rebuilds update v2's snapshots
and leave this archive unchanged. Downloads continue to use installed shared
Python implementations; the archived interface's original fixed-sample specs
remain supported.

`archive-manifest.json` records baseline and archived checksums. The legacy
browser workflow test defaults to this archived URL; the v2 workflow has its
own test script.
