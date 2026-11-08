# Circuit/CUDA audit closure

All three findings from the [043–046 audit](CANONICAL-KERNEL-CIRCUIT-CUDA-AUDIT.md)
are closed in the requested order:

1. [E03 result validation](047-circuit-result-admission-fix/README.md), d6e8756.
2. [E01 compiled overflow failure](048-circuit-numerical-failure-fix/README.md), 02d890a.
3. [E02 inactive control admission](049-circuit-control-admission-fix/README.md), 5855049.

Final qualification: **257 tests pass; 12/12 audit groups pass**. The independent
1,152-case circuit mathematics, 360 native comparisons and 336-configuration
policy matrix retain their baseline receipts exactly. All 32 captured ordinary
controller/rule/DEM output ledgers and two 64-shot timing-fixture ledgers are
byte-identical before and after the changes. The original failure evidence is
preserved, with new regressions and source hashes recorded separately.

The changes validate public results, detect nonfinite NMS intermediates before
clipping, and reject non-default inactive controls. Valid policy identities,
ordinary BP equations and generated ledger formats are unchanged. Only the two
circuit policy modules changed in production; CPU code-capacity and GPU source
remain unchanged, preserving their qualified scope without a new GPU allocation.

These fixes complete the audit's bounded pre-HTML work. The documented compatible
subset can be used for HTML development. Release packaging remains skipped;
source-curve reproduction and the outstanding publication gates remain separate.

See the [implementation summary](../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/SUMMARY.md)
for commands, red/green evidence, timing scope and retained hardware qualification.
