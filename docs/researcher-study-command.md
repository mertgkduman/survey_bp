# One command for BP policy studies

Install the package from a checkout with `python -m pip install -e .`. The public Python API is `from bp_registry.study import ensure_study`; the installed command is `bp-registry`.

## Use the published BB72 BeamSearch/RelayBP study

```bash
bp-registry data/studies/fair-beam-relay-css-v2.json \
  --decoder examples/bb72-relay-decoder.toml --workers 8
```

The command checks the publication manifest, every package file, and the decompressed shot ledgers before returning the selected RelayBP results. If the complete package is absent, the **same command** runs selection, freezes the selected profiles, runs evaluation, replays the evidence, packages it, and returns the result. A nonempty incomplete campaign directory is rejected so the command does not silently overwrite interrupted evidence; use the shard runner to inspect or resume that directory.

Change `--decoder` to `examples/bb72-beam-decoder.toml` for BeamSearch. The result package is shared because the registered campaign evaluated both methods on matched samples. The decoder file can choose `method = "beam"` or `"relay"`, `damping = 1.0` or `0.5`, and `profile = "selected"`, `"i05"`, `"i10"`, or `"i20"`. The frozen design fixes the code, noise rates, budgets, topology, and Relay memory interval; changing those is a **new study**, not a cached result of this one.

## Compose registered canonical CSS policies

```bash
OMP_NUM_THREADS=1 bp-registry examples/three-qubit-study.json \
  --decoder examples/three-qubit-decoder.toml \
  --results-root ./my-results
```

The study JSON specifies code, artifact identity, noise, physical sample namespace, environment, budgets, and evidence status. The decoder TOML names **all seven** policy roles: update, schedule, state memory, intervention, stopping, selection, and postprocessing. Each role accepts a registered `kind` and any fields in the strict policy schema. The command writes the expanded, validated JSON manifest beside the ledger and result. Unknown policies and incompatible combinations fail before sampling. The example is a two-shot development fixture marked `not_assessed`; its output is not a decoder performance estimate.

For a commented V2C damping policy, use `examples/three-qubit-memory-study.json` with `examples/three-qubit-damped-decoder.toml`. Its `[[memory.bindings]]` table specifies the coefficient, target, order, lifecycle, and refresh boundary. Changing `gamma` produces a new result identity.

Results are addressed by a hash of the effective manifest and package source. On another call, the command verifies the cached ledger and result before returning `status: reused`; otherwise it produces and verifies them and returns `status: computed`. Changing comments or whitespace in the policy file leaves the effective decoder unchanged. Changing a policy, budget, artifact, environment, or engine source changes the result identity. An explicit `physical_sample_identity` in the study keeps physical samples matched across decoder files.

Use the same API from Python:

```python
from bp_registry.study import ensure_study

result = ensure_study(
    "examples/three-qubit-study.json",
    "examples/three-qubit-decoder.toml",
    results_root="my-results",
)
print(result["status"], result["result"]["denominators"])
```

TOML is the recommended hand-written policy format because it permits `#` comments. JSON policy files are accepted and have identical semantics. Policy files compose **registered** implementations; they cannot define a new update equation by naming a Python module or callable. A new algorithm requires a reviewed policy implementation and compatibility rule in the engine before it can be selected from a file.

The public canonical runner supports schema v2/v3 CSS compositions and schema v4 ordered memory bindings. For v4, place `memory` and optional `relay` sections in the decoder file along with the seven roles; keep them out of the study JSON. The registered BB72 BeamSearch/RelayBP campaign uses its own source-sealed backend through this same command. Phase 5 intervention controls, new policy implementations, and faithful circuit-level studies need explicit interface support and qualification before this command can claim them.
