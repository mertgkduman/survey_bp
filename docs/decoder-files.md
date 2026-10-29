# Decoder files

A decoder file records **how to decode**. A study or campaign file records the
code, physical noise, sampling seed, shot count, and evidence location. Keeping
these separate makes policy comparisons on the same sampled errors possible.

## General registry command

For the public `bp-registry` command, put a hand-written TOML decoder under
`examples/` or `literature_policies/<paper>/decoders/`. JSON is also accepted.
Pass it with `--decoder` alongside a study JSON:

```bash
OMP_NUM_THREADS=1 bp-registry examples/three-qubit-study.json \
  --decoder examples/three-qubit-decoder.toml --results-root ./my-results
```

The file names registered policies for seven roles: update, schedule, state
memory, intervention, stopping, candidate selection, and postprocessing. The
engine validates each role and its compatibility with the others before
sampling. See the [command guide](researcher-study-command.md) and the
[example decoder](../examples/three-qubit-decoder.toml) for the exact TOML
schema. A decoder file cannot load an arbitrary Python callable. Adding a new
update rule requires an engine implementation and compatibility rule.

For a new controlled comparison, start with an existing decoder file, change
one policy field at a time, and keep the study's `physical_sample_identity`
fixed. The expanded effective manifest is written beside the result ledger.
The manifest, rather than a filename alone, identifies the run. Numeric policy
details such as resolution, message clipping, damping location and coefficient,
check rule, stopping, and candidate selection should be explicit whenever they
matter to the comparison. The [numerical profile guide](numerical-profiles.md)
defines the supported floating and fixed-resolution boundaries.

## Frozen files in a paper reproduction

Some source-specific studies have their own strict, data-only decoder schema
because they execute a pinned compiled kernel directly. The
[Yao vanilla BP study](../data/reproductions/yao-2312-10950-vanilla/README.md)
uses four JSON files under its `decoders/` directory. For example:

```json
{
  "schema": "vanilla-bp-decoder-v1",
  "id": "bp4_v2",
  "family": "bp4",
  "check_rule": "sum_product",
  "numerical_profile": "quaternary-bp4-f64-v2-undamped",
  "message_resolution": "float64",
  "damping_old": 0.0,
  "check_cap": null,
  "product_epsilon": 1e-10,
  "max_iterations": 100,
  "prior": "depolarizing_joint_p0_equals_physical_p",
  "candidate": "first_syndrome_matching_hard_decision_after_at_least_one_sweep",
  "reference_role": "canonical_v2_numerical_adaptation"
}
```

These files are consumed by that study's `run.py`, **not** by the public
`bp-registry --decoder` command. The runner accepts only its four named files
and checks their supported values. It records the file bytes and resolved
kernel profile in each shard manifest. The campaign also hashes the files and
implementation sources before launch; editing any frozen file invalidates a
task. Create a new campaign identity for a changed policy, and retain the old
results as a separate experiment.

When reading results, inspect the decoder JSON, the shard `manifest.json`, and
the merged report together. The JSON states the requested policy, the manifest
states what actually ran, and the per-shot ledger records outcomes. A source
paper's name on a file is provenance, not a claim of numerical identity with
an undocumented implementation.

The [A5/B2 BP4 tuning study](../data/reproductions/yao-2312-10950-bp4-tuning-p006/README.md)
uses the same separation between decoder policy and sampled errors. Its
`decoders/` directory contains frozen candidate registries and selected
per-code files; its study-specific `runner.py` reads them, and its stage plans
pin their bytes. The selected files are not accepted by the public
`bp-registry --decoder` command. They record physical `p=0.06` separately
from decoder prior `p0`, so a tuned prior need not equal the sampling rate.
Its [paired fairness control](../data/reproductions/yao-2312-10950-bp4-tuning-p006/fairness_t100/README.md)
freezes an additional registry for equal-cap and approximately equal-work
comparisons; those files use the same study-specific runner contract.

The [tuned Q-BPGD study](../data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/README.md)
pins each selected BP4 decoder file by hash, then uses its prior and numerical
profile for every Q-BPGD sweep. Its per-code JSON files also record the
ten-sweep decimation block, fixation epsilon, and round cap. Standalone BP4
iteration caps are not reused as Q-BPGD round settings. The study runner and
compiled development backend consume these files; the public registry command
does not.
