# Paper-grid and execution decisions

The pinned source plot `figs/BSClDSC.273.82C.ps` has measured abscissae
.010, .013, .020, .030 and .040. Integer vector coordinates and approximate
ordinates are retained in `source_points.json`, with the archive and figure
digests. Approximate plotted values are not raw author counts.

The requested correction retains both codes and three existing arms. Joint
depolarizing rates are 1.5 times the source's binary crossover probabilities,
including .0195 exactly. The plan and experiment IDs use p*100000, preventing
rounding .0195 to .020. Source targets attach only to length-274 unicycle SP;
the other code/decoder arms remain controlled comparisons.

The original two-hypothesis implementation spends most low-noise time on a
branch that cannot win. Extended incidence codes have classical distance
>=q+2: even-line parity needs q+2 support points, and odd-line parity needs
q+1 support points plus the extra bit. The qualified matrices independently
verify all required incidence counts and overlaps. Any two syndrome-valid
candidates differ by such a codeword. A first valid candidate of weight w
with 2w<q+2 is therefore strictly lighter than every candidate from the other
hypothesis. Branch order uses syndrome majority and independent branch state;
when both branches run, likelihood and extra-bit-zero ties remain unchanged.

This exact optimization changes executed work. It is explicit in the frozen
controller, display parameters and per-shot branch vectors; skipped branches
record zero. New work cannot be pooled with the unpruned campaign. Quantum
block failures and classical block errors are both retained: the latter also
include stabilizer-equivalent recoveries. No classical confidence interval is
borrowed from quantum-failure stopping when those counts differ.

No existing kernel, old frozen runner or old plan is edited. The new runner
reuses their qualified code, sampler and ledger logic through a separate module
instance. Independent worker batches retain exactly the contiguous stopping
prefix and remain bounded by the shot cap. Unit checks cover real selected
candidate equivalence, both skipped-branch cases, the equality boundary, ties,
invalid candidates, parallel order, resume and work counters.

The old .04–.10 dataset is retained in the raw catalog and retired through a
validated data-only `public_retired_dataset_ids` list. The common projection
therefore hides it in all public plots, tables, exports, input lists and saved
choices. New paper-rate curves still need two measured rates. A separate
sampling role and controller identity protect old/new evidence semantics.

Inline plan review passed: the three implementation units cover the exact
grid, execution/statistical contract and public catalog integration. No agents,
automatic model escalation or model configuration changes were used.
