# BeamSearch author circuit fixtures

The 38 tracked `.stim` circuits in the [BeamSearchDecoder source repository](https://github.com/ionq-publications/BeamSearchDecoder) at commit `084a475b05fb64308103317a1ce5a0c4b0be58aa` are preserved byte for byte in `beamsearch-circuits.tar.gz`. `manifest.json` records each original filename, byte count, SHA-256 digest, and the archive digest. `bb144-memory-z-p005.stim` is a direct copy of the named BB144 representative in the manifest.

The source repository declares **CC BY-NC-SA 4.0**; its `LICENSE` and `THIRDPARTY-LICENSES` files are retained here. These circuit data are separate source artifacts, not a license declaration for the platform code. Before redistribution or publication packaging, review the applicable terms and attribution for this bundle.

To extract the complete source inventory:

```bash
mkdir -p /tmp/beamsearch-circuits
tar -xzf data/circuits/beamsearch-084a475b/beamsearch-circuits.tar.gz -C /tmp/beamsearch-circuits
```

Their presence does not establish the exact circuit, decoder settings, or statistical stopping rule used for any reported paper curve.
