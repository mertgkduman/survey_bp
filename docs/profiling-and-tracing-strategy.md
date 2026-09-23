# Profiling and tracing strategy (D-20)

## Purpose, scientific value, and cost

Profiling and tracing make a canonical execution auditable when a result needs more explanation than an outcome and a headline iteration count. They are observations, not decoder controls: they must not change a candidate, work vector, lineage, termination, or selection. Their scientific value is to separate algorithmic work from process-local runtime, make replay agreement testable, and preserve bounded diagnostic evidence. Their cost is runtime, memory, I/O, and potential observer perturbation; measure that cost explicitly instead of folding it into clean execution time.

This is a development-only strategy, not a campaign default. It gives no publication quota, sampling rate, statistical tolerance, or compute allocation. Publication campaigns must declare their own values rather than inheriting Phase 2 defaults.

## Evidence levels and bounded traces

All canonical runs retain sparse structural evidence: durable begin, attempt, candidate, selection, work, runtime, missingness, and termination facts. This is the minimum evidence needed to reconstruct a result. Optional traces add iteration and edge observations as sidecars.

| Level | Implemented control | Use and limitation |
| --- | --- | --- |
| off | `TracePlan.level="off"` | no sidecar; structural evidence remains |
| full | `TracePlan.level="full"` | every requested optional observation, only for small diagnostic development cases |
| filtered | `TracePlan.level="filtered"`, `iterations`, `edges` | selected iteration or edge evidence, for rare or race-sensitive investigation |

`TracePlan` confines `relative_dir` under its declared root. `max_records` and `max_bytes` are hard quotas. A sidecar carries `truncated` and `dropped_records`; the truncation fact itself is retained even if prior optional records must be removed to fit the byte cap. Sidecars are content-addressed by SHA-256 and linked with path, digest, record count, byte count, and truncation status. The semantic trace digest is content identity for replay comparison: it removes measurement-only fields and is not authenticity or a population measurement.

Low-overhead bounded traces are particularly appropriate for race-sensitive behavior that cannot safely be reproduced by a second run. They remain observational: a trace sink can drop optional records but has no decoder control-flow interface.

## Local profiling facts and missingness

`ProfilingPlan` defaults to enabled `low_overhead` observation; it can be disabled, made strict with `required`, or raised to `representative` with `track_python_allocations`. `LocalProfiler` emits typed `ProfileMeasurement` evidence: `runtime.wall_time` from `time.perf_counter_ns`, `process_cpu_time`, platform-qualified `peak_host_memory`, concurrency, machine adapter identity, and explicitly unavailable backend device facts; `adapter_overhead`, measured with an empty adapter call and reported apart from observed run duration; and `python_allocation_peak` from `tracemalloc` only when requested, not host RSS.

Only positive numeric thread counts from `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` are retained. Every unavailable measurement has method, scope, unit, precision, and a reason. Do not replace unavailable data with zero, guess child-process or device measurements, or serialize arbitrary environment values. In a strict plan, an unavailable required fact raises `ProfilingRequirementError` rather than quietly satisfying the request.

## Cohorts and what can be estimated

Use three separate cohorts, never a single selected example for every claim:

1. **clean**: the full clean population supplies outcome and ordinary runtime summaries, with `selection_reason="full_clean_population"`.
2. **representative**: a prespecified, paired clean/profiled sample for detailed profiling and overhead estimation. It records `selected_before_outcome`, stratum, and `inclusion_probability` before outcomes; only this form can be `population_estimate_eligible`.
3. **diagnostic**: targeted tail, rare-event, divergence, or bounded-trace replays for explanation. It records a selection reason and is not eligible for population inference.

Diagnostic evidence is not a population estimate. Outcome-conditioned or post-hoc selection must not be plotted as an unbiased population profile unless its selection probabilities and a valid weighting plan are declared separately.

## Pairing, replay, agreement, and divergence

Create a `ReplayLink` between clean and profiled attempts with distinct `clean_run_id` and `profile_run_id`, plus `manifest_identity`, `sample_identity`, `decoder_randomness_identity`, `ordering_identity`, cohort, profiling level, and `overhead_ns`. Compare `semantic_agreement` only over `candidate`, `termination`, `work`, `lineage`, and `semantic_trace_digest`; timing and other measurement fields are deliberately excluded from semantic identity.

An agreement is necessary, but not by itself sufficient, for a representative population statement. A mismatch is retained as `diagnostic_divergence` with `retained_divergence` retention. It must never be silently dropped or described as a measurement of the clean execution.

## Plotting and reporting

For every plot, state its cohort, denominator, profile level, sampled strata, inclusion probability when applicable, timing scope, and missingness counts. Use separate panels or marks for clean population outcomes/runtime, paired representative profile measurements and adapter overhead, and targeted diagnostic examples. Show truncated trace counts and unavailable counters; do not impute a zero or draw an unlabelled aggregate.

Development evidence is not a reproduction claim. A plotted two-shot fixture, selected trace, or profiler example is labelled `development_fixture` and `not_assessed` unless a separate source-faithful/statistical protocol establishes otherwise.

## Retention and review

Retain `paired_summary`, `bounded_trace`, or `retained_divergence` explicitly. Keep selected candidates in full; rejected payloads require a bounded trace, rare-event cohort, or declared candidate-retention policy. Preserve hashes, lineage, reasons, validations, sidecar links, and missingness facts even when a large optional payload is dropped. Revisit quotas, cohort rules, and plotting templates before any campaign with allocated compute resources.

Implementation anchors: `src/bp_registry/canonical/profiling.py` (`ProfilingPlan`, `ProfileMeasurement`, `CohortSelection`, `ReplayLink`) and `src/bp_registry/canonical/tracing.py` (`TracePlan`, `TraceSink`, `semantic_digest`).
