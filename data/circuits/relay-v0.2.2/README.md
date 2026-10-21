# Relay-BP v0.2.2 circuit fixtures

The 672 original Stim circuit files are preserved byte for byte in `relay-circuits.tar.gz`. `manifest.json` records every original relative filename, byte count, SHA-256 digest, the archive digest, the upstream tag and commit, and the license identity. Four files are also copied at the top level for immediate use; their names map to original paths in the manifest.

Source: [trmue/relay](https://github.com/trmue/relay), tag `v0.2.2`, commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`. Original license: Apache-2.0, retained in `LICENSE.txt`. These are the source repository's test circuits; a circuit's presence here does not by itself identify a particular plotted paper point or all of its decoder settings.

To extract the complete set into a separate directory:

```bash
mkdir -p /tmp/relay-circuits
tar -xzf data/circuits/relay-v0.2.2/relay-circuits.tar.gz -C /tmp/relay-circuits
```

Use the manifest to select exact basis, rounds, distance, error rate, and source filename. The circuit decoder integration and its limitations are described in [the circuit kernel guide](../../../docs/circuit-kernel.md).
