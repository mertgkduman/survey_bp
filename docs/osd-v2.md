# Canonical OSD v2

`bp_registry.postprocessing.osd_v2.Osd` is an explicitly selected successor to
the frozen uniform processor. Existing plans still import
`postprocessing/osd.py`; their implementation hashes, raw outcomes and replay
contracts are unchanged. This qualification does not relabel the historical
failed Phase 7 standalone-native admission.

```python
from bp_registry.postprocessing.osd_v2 import Osd, AffineBasisCache
from bp_registry.postprocessing.bp_osd_v2 import CanonicalBpOsd

processor = Osd(H_csr, method="OSD_CS", order=10,
                channel_probabilities=per_bit_probabilities)
result = processor.decode(syndrome, signed_posterior_llr,
                          evidence_mode="fast", materialize_candidates=False)
save_json(result.ledger)  # every call, together with recoverable original inputs
replayed = processor.replay(syndrome, signed_posterior_llr, result.ledger,
                            materialize_candidates=True)

pipeline = CanonicalBpOsd(processor, max_iterations=100, alpha="roffe")
shot = pipeline.decode(syndrome)  # unchanged canonical min-sum sweep
save_json(shot.ledger)            # includes BP work and the optional OSD ledger
```

`save_json` denotes the experiment's durable per-shot ledger writer. This API
returns mandatory evidence; callers must persist it under their manifest and
retain/reconstruct original matrix, priors, syndrome and posterior inputs.
The decoder has no simulation truth input. A syndrome-valid recovery may still
have a logical error; the independent CSS/observable evaluator decides that.

## Algorithm and scores

The reference is the MIT-licensed
[quantumgizmos/ldpc OSD implementation](https://github.com/quantumgizmos/ldpc/blob/d3429964cd4ffe1abfc041c6ec8b8425cb174f40/src_cpp/osd.hpp).
We preserve its candidate family and source score while making stable ties
explicit. The reference factorizes once and repeatedly solves modified
syndromes. Affine reuse instead computes the response to each free-bit flip
once: `x(f) = x0 XOR D(f)`. Singles use one direction; pairs use two. No
candidates are pruned and no earlier winner terminates the search.

1. Sort **signed** posterior `log(P0/P1)` ascending. Equal LLRs retain original
   column ID order. This is not an absolute-LLR sorting policy.
2. OSD0 retains the historical partial pivot prefix sufficient to span this
   syndrome. It uses one triangular solve; its pivot count need not be rank(H).
3. CS computes a full independent pivot basis in that order. Enumerate x0,
   **all** free-column singles, then `(0,1), (0,2), …, (depth-2,depth-1)` pairs
   within the first `depth` free columns. Candidate count is
   `1 + (n-rank(H)) + depth*(depth-1)/2`.
4. Scan scores in that order and replace the winner only for `<`, preserving
   the first minimum across block boundaries. No epsilon tie merging is used.

Probabilities are immutable original-channel inputs, cached in the constructor.
They do not come from the final posterior. Probabilities must lie strictly
between zero and one and produce finite float64 weights under the selected
score convention. Two scoring conventions are explicit:

| `score` | Per selected bit | Interpretation |
|---|---|---|
| `source_log_inverse_p` (default) | `log(1/p_i)` | Pinned native source convention |
| `bernoulli_log_odds` | `log1p(-p_i)-log(p_i)` | Independent-bit negative log likelihood, dropping a candidate-independent constant |

These conventions can choose different winners on nonuniform channels.
Candidates and reliability ordering remain the same. Each weighted score is a
float64 left fold over selected **original column IDs ascending**. Fastmath,
reassociation and weighted delta-score subtraction are excluded because they
can alter near-ties. The prefix-sum oracle and native source independently check
this behavior. For identical probabilities and positive weights, the processor
retains integer Hamming scores and packed popcount. ML at p=1/2 or above uses
the weighted path; negative weights are allowed there.

## Matrix ownership and cache

Dense integer binary arrays and SciPy CSR/CSC inputs are accepted. Sparse input
is never converted to a dense H. Sparse duplicates must canonicalize to binary
values; nonbinary multiplicities are rejected rather than silently reduced
modulo two. Shape and sorted CSR row pointers/indices form one immutable exact
matrix key. CSR ndarray views share those bytes. There is no retained dense H.

`matrix_storage="sparse"` keeps CSR only and packs rows when factorization is
needed. `"packed"` also retains packed original rows. `"auto"` compares CSR and
packed byte counts, favoring the smaller original representation; it is a
memory heuristic, not a runtime crossover claim. Elimination uses packed rows
in both cases because sparse matrices can fill in. Original-H checks use CSR
for sparse storage and packed parity for packed storage.

`AffineBasisCache(max_bytes=..., max_entries=...)` is opt-in. Pass it as
`cache=cache` to share full CS bases across decoder instances. A key contains
the **exact canonical matrix bytes and exact complete stable column-order
bytes**, rather than relying on digest equality. Values retain reduced rows,
the complete row transformation, pivots/free order and packed affine directions.
For a new syndrome the transformation reconstructs its reduced RHS. Different
channel weights and CS depths can share a basis; different matrices/orders
cannot. OSD0 bypasses it because its stopping prefix depends on the syndrome.

The thread-safe LRU bounds retained array payloads plus exact key bytes and
entry count. Python object/container overhead is separately measured, not
included in `max_bytes`. Oversized entries are rejected. Snapshots and temporary
factorization can transiently use more memory than the retained-cache budget.
Key bytes are charged per entry conservatively even when immutable keys share
storage.
Warm repeated-order gains must not be presented as changing-order gains; a cold
miss additionally computes/stores the transformation. See the measured hit
rates and crossover results before enabling it in a campaign.

## Evidence and replay

Implementation `weighted-streaming-osd-v2`, evidence `osd-evidence-v2`, and work
schema `osd-work-v2` are explicit. Both evidence modes compute exactly the same
semantic digest, including in nonuniform channels:

| Mode | Original-H checks | Candidate digest | Candidate materialization |
|---|---|---|---|
| `fast` | Selected winner | All candidates and weights | Optional, default off |
| `full` | Every enumerated candidate | All candidates and weights | Optional, default off |

Candidate generation, scoring and SHA256 are block-streamed. Only the base,
single directions, a bounded candidate block and the O(candidate count) scores
are needed without materialization. Weights remain available until their digest
stage and in the result. Pair storage does not scale as candidate count times
matrix width. The default block contains at most 512 candidates; `block_size`
can select a different memory/latency balance. Full evidence can be used without
retaining all candidates.

Digest ordering is **all** original-coordinate candidate-major little-endian
uint64 rows, including zero tail padding, followed by **all** score bytes.
Uniform weights are little-endian int64; weighted scores are little-endian
float64. No interleaving per block is allowed. Uniform positive-channel digests
are byte-for-byte compatible with v1. Score convention/encoding and every input
identity are separately bound into the semantic ledger to disambiguate bytes.

The ledger binds method/depth, matrix/channel/syndrome/posterior/order/pivot/free
identities, candidate count, winner, weights and set digest. Operational fields
include evidence/validation/materialization modes, ablation settings and actual
work. The complete ledger has a canonical JSON integrity digest. Replay checks
it and recomputes all semantic fields. Cache-dependent work and timings may
differ during replay; this does not change scientific outputs. Altered inputs,
score rules or ledger payloads are rejected. Timings are operational measurements
and are excluded from deterministic semantic digests.

## Work and measurements

Counters count named operations actually executed, with explicit units; they
are not an estimate of CPU instructions or FLOPs. Cache hits report zero
elimination/response work and nonzero transform application instead. Early
validation failure counts only completed work before the error, which is not
published as a successful result.

| Counter group | Unit and boundary |
|---|---|
| `pivot_bit_tests` | Tested packed pivot bits, including above-diagonal CS reduction |
| `row_xor_words`, `row_swap_words` | uint64 row positions XORed or swapped |
| `syndrome_row_xors` | RHS bits XORed during elimination |
| `transform_*_words` | uint64 transformation positions XORed/swapped/applied |
| `back_substitution_words` | Packed row-word parity terms in triangular solves |
| `response_scan_words`, `response_pivot_bit_tests` | Packed words traversed or scalar coefficient probes for single directions |
| `response_coefficients` | Live free-to-pivot coefficients used |
| `candidate_xor_words` / `candidate_xor_bytes` | Packed-word or byte-per-bit affine XORs |
| `score_popcount_words`, `score_bit_tests`, `score_additions` | Packed Hamming words, scanned bits, weighted selected-bit additions |
| `byte_score_*` | Corresponding byte-per-bit ablation work |
| `validation_words` / `validation_edges` | Original-H parity terms evaluated |
| `candidate_hash_bytes`, `weight_hash_bytes` | Exact byte counts fed to the candidate-set digest |
| `matrix_pack_edges`, `matrix_words_copied` | Original sparse edges packed, packed working matrix positions copied |

The work ledger also records counts, bounded block payload, materialized bytes,
retained score/matrix/cache payloads and cache outcomes. Disjoint stage timers
cover validation/input binding, sorting, packing, cache lookup, factor/transform,
responses/store, base solve, generation/scoring, original-H validation, hashing
and ledger/snapshots. `total` includes wrapper gaps; stage sums cannot exceed it.
These timers perturb small calls. Cold construction/JIT are separated in the
benchmark, with full processor calls timed externally as well.

Historical v1 counters remain unchanged. For example, its
`affine_pair_xor_words` is a one-word-per-pair proxy; the new
`candidate_xor_words` records one XOR per single and **two** XORs per pair word.
Do not pool those fields or reinterpret earlier ledgers as v2 measurements.

The pipeline records BP sweeps and `2 * edges * sweeps` directed edge updates
separately from OSD work. Its whole-call timer includes evidence and activation;
the BP/OSD timers expose each stage. It does not convert GF2/search operations
into BP iteration equivalents.

## Reproduce qualification and benchmark

Run tests:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_osd_v2.py tests/test_osd_v2_benchmark.py tests/test_uniform_osd.py
```

Run `scripts/benchmark_osd_v2.py --run` under a **single-CPU allocation** with
OMP/OpenBLAS/MKL threads fixed at one, the clean pinned source in
`.git/osd-upstream`, and the weighted native bridge in the output directory.
Use a new output directory for later runs; do not replace a sealed report.
`--verify` checks the evidence seal and implementation identities.
For the retained initial run, `--verify --historical --output
data/benchmarks/osd-v2` checks its archived source snapshots. The final qualified
run and default verification path are `data/benchmarks/osd-v2/qualified`.

The fixture corpus seals sampled errors and actual canonical BP nonconvergence
states; errors are only used to construct observed syndromes and independent
checks. The timed OSD interfaces receive the same unique, stable-order-equivalent
ranks, while full equivalence also checks the actual posteriors. Native timing
excludes candidate tracing; v2 timing includes mandatory evidence. End-to-end
timings rerun canonical BP and activate OSD on its actual failure, for both
failure-conditioned and separate mixed-shot inputs. No Monte Carlo LER or
threshold conclusion follows from this bounded qualification corpus.

Measurements use alternating orders and retain every round, stage/work examples,
cache statistics, construction/storage crossover, fresh-process peak RSS and
incremental traced allocation. RSS high-water reset availability is recorded;
Python tracing may omit native allocation. Read memory and timing scopes with
the values. See [the qualified benchmark](../data/benchmarks/osd-v2/qualified/QUALIFICATION.md)
for measured benefits, regressions and generalizability limits.
