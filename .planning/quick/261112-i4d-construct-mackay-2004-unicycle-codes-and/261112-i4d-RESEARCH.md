# Source and implementation decisions

Selected MacKay, Mitchison and McFadden (2004), quant-ph/0304161v3, from the
existing foundational-paper list in spike 055. Source archive checksum and
TeX-member checksums are in `data/reproductions/mackay-0304161-unicycle/source.json`.

Construction U provides reproducible compact inputs. Length 74 uses the
explicit difference set; length 274 uses a qualified project-generated perfect
difference set. Independent integer overlaps, GF(2) ranks and paired logicals
verify [[74,18]] and [[274,110]]. Other paper constructions remain outside this
initial campaign; random author instances must not be inferred.

The two-hypothesis unicycle decoder wraps the existing canonical binary SPA
kernel. Candidate selection uses only syndrome and the full prior likelihood,
including the conditioned bit. No hidden truth enters decoding. The controlled
ordinary-BP arm measures the effect of the wrapper. Joint Q-BP is a separate
controlled comparison, with the previous campaign's depolarizing marginal
mapping and numerical settings.

The paper does not supply an iteration cap or exact floating-point conventions
for this experiment. The previous 88,200 total-sweep ceiling is retained, split
equally between the two unicycle hypotheses. Optional user clarification was
offered before freezing; no reply changed this stated assumption. Source plot
metrics and channel differ, so no source-curve agreement is claimed.

Reuse the completed campaign's durable ordered-prefix ledger and exact
stopping intervals without modifying its pinned implementation. Add explicit
branch vectors and directed-update validation. Evaluate logical signatures
using packed matrices rather than the old <=63-logical bitmask helper.

Use the existing data-only catalog extension mechanism. The common active-view
filter hides pending/one-rate curves and their inputs. Decoder display must
recognize the unicycle controller before its existing Q-BPGD case, and curve
identity must retain the controller to prevent pooling ordinary/split BP.

Inline plan review: coverage and executable verification paths checked. The
construction/runner, catalog publication and verification form three execution
units. Long Monte Carlo execution is delegated to Slurm jobs with an afterany
audit; it is recorded as running until terminal ledgers are actually verified.
No subagents or model-configuration changes were used.
