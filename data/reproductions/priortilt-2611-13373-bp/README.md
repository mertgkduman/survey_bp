# Ordinary and tuned BP on the PriorTilt benchmarks

The campaign adds ordinary and tuned flooding min-sum BP at all 13 XZ
code/rate combinations from Fig. 1 and the BB144 XYZ point at p=.003 from Table 4.
Each decoder point has 20 CPUs shared between its two memory streams. Both
methods use 18,080 sweeps maximum, a first syndrome-consistent stopping rule,
and the last hard decision on exhaustion. This compares to the XZ RelayBP
budget. The original XYZ PriorTilt and RelayBP-5 budgets are about twice as large.

Ordinary BP sets damping=0, scaling=1 and offset=0. Tuned BP uses the same
canonical float64 sweep and hard decisions (LLR zero maps to one), and searches
those three parameters. V2C damping uses the declared old-message weight.
Check magnitudes are scaled after subtracting the offset and clipping at zero.

Tuning uses p=.003 independently for BB144 XZ, BB70 XZ, GB102 XZ and BB144 XYZ.
The BB70 and GB102 training-only circuits rescale the noise arguments of the
released p=.002 circuits. The same construction recovers the noise arguments,
gate targets and structure at every released rate for each memory basis.
The search tests 24 settings on 128 shots per basis, then up to six on 512 and
three on 2,048. Equal denominators and shared shots are used within each round,
with independent seeds across rounds. The neutral setting is carried through.
The final choice is based on observable logical errors. Among candidates within
one error of the minimum, fewer iterations wins. Evaluation uses separate
samples and applies the selected settings across that code and mode's grid.

Evaluation takes ordered slices from the existing sealed shared Stim streams,
extending the streams with their original sampling contract when needed. Each
basis stops at 20 observable errors or 100 million shots. Every retained shot
records an independently decoded fault candidate, observable outcome, work and
decoder timing. Full worker audits verify original detectors, logical outcomes,
ledger bindings, and endpoint replays. Speculative shots have separate accounting.
The report uses audited pairs and preserves each basis's counts. It reports
concurrent instrumented decoder timing and the mean directed edge updates and
iterations per shot.

- [XZ paper comparison](../priortilt-2611-13373/RESULTS.md)
- [XYZ paper comparison](../priortilt-2611-13373-xyz/RESULTS.md)
- [BP results](RESULTS.md)
- [Source paper](https://arxiv.org/html/2611.13373v1)

The training-only circuits are modifications of the released PriorTilt circuits.
The original circuit attribution and license apply.
[Source license](../priortilt-2611-13373/SOURCE-LICENSE)

An ordinary BP shot in the initial dispatch overflowed float64 on a long
nonconverging trajectory. The resumed study uses a versioned numeric profile
that reduces the exponent of all messages, priors and the offset together by
400 when message magnitude reaches 2^480. Min-sum with the declared damping
and check rules is homogeneous under this common scaling. This preserves the
iteration cap and detector and observable tests, with usual floating-point
limits for values below the representable range. Per-shot rescale counters
and aggregate counts are retained. Initial dispatch ledgers are archived
separately, and the replacement starts from the same sealed evaluation inputs.
