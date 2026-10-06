# Phase 10: Correlated Quaternary Execution - Discussion Log

> **Audit trail only.** Research, planning, and execution use `10-CONTEXT.md` for decisions.

**Date:** 2026-10-06
**Phase:** 10-correlated-quaternary-execution
**Areas discussed:** Supported codes, Joint channel input, Policy coverage, Q-BPGD ambiguities

The user selected all four areas. Every numbered decision selected option 1. The user added aSCED during policy coverage, then chose its full paper method and executable author reference.

---

## Supported codes

### 1. Which public execution boundary should Phase 10 support?

| Option | Description | Selected |
|--------|-------------|----------|
| General stabilizer codes | Run general stabilizer checks and compile CSS inputs into the same model. | ✓ |
| CSS codes first | Expose only CSS inputs in this phase. | |
| Other | Free-form preference. | |

**User’s choice:** General stabilizer codes now, with CSS codes compiled into the same Pauli model.

### 2. Should a researcher be able to use an existing validated CSS artifact directly?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, compile it internally | Accept existing CSS artifacts and compile them internally. | ✓ |
| Require a Pauli artifact | Require a new Pauli artifact from the researcher. | |
| Other | Free-form preference. | |

**User’s choice:** Yes; compile it internally, preserving identity and declared check order.

### 3. Should decoding be allowed without a supplied logical-operator basis?

| Option | Description | Selected |
|--------|-------------|----------|
| Allow with limited logical detail | Use stabilizer membership to classify outcomes; specific logical action unavailable. | ✓ |
| Require a logical basis | Reject runs without a logical-operator basis. | |
| Other | Free-form preference. | |

**User’s choice:** Yes; classify exact, stabilizer-equivalent, or logical failure from independent stabilizer membership, while leaving the specific logical action unavailable.

**Clarification:** The user asked how classification works without a logical basis. The explanation was that a syndrome-valid residual lies in the normalizer; stabilizer membership distinguishes degeneracy from logical failure, while a basis identifies the particular logical action.

### 4. What evidence should demonstrate general stabilizer support?

| Option | Description | Selected |
|--------|-------------|----------|
| End-to-end non-CSS example | Exercise a non-CSS code through manifest, decoder, evaluator, and ledger. | ✓ |
| Fixtures only | Use internal non-CSS fixtures only. | |
| Other | Free-form preference. | |

**User’s choice:** A small non-CSS code must run end to end through the public manifest, decoder, evaluator, and ledger, alongside algebraic fixtures.

---

## Joint channel input

### 1. How should researchers specify the physical Pauli channel?

| Option | Description | Selected |
|--------|-------------|----------|
| Named and explicit forms | Accept a named depolarizing rate or an explicit four-state table. | ✓ |
| Explicit table only | Require a four-state table for every run. | |
| Other | Free-form preference. | |

**User’s choice:** Accept named depolarizing p and explicit I/X/Y/Z probability tables; persist the resolved probabilities in either case.

### 2. Should explicit channels allow different probabilities per qubit?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes | Accept a shared table or distinct rows for each qubit. | ✓ |
| One shared distribution only | Accept one uniform table only. | |
| Other | Free-form preference. | |

**User’s choice:** Yes; accept one shared distribution or declared per-qubit distributions.

### 3. What happens when a declared channel assigns zero probability?

| Option | Description | Selected |
|--------|-------------|----------|
| Exact sampling, explicit decoder smoothing | Sample physical zeros exactly and require declared smoothing for the decoder. | ✓ |
| Reject zero-prior decoder runs | Allow zero sampling fixtures but reject zero-prior decoder runs. | |
| Other | Free-form preference. | |

**User’s choice:** Sampling preserves exact zeros; a log-domain decoder requires explicitly recorded smoothing before decoding with zero priors.

### 4. How should physical error rate be represented for a per-qubit probability table?

| Option | Description | Selected |
|--------|-------------|----------|
| Per-qubit non-identity rates | Record 1-P(I) per qubit; scalar p only for a named uniform channel. | ✓ |
| Average rate | Also call the average of per-qubit rates the scalar p. | |
| Other | Free-form preference. | |

**User’s choice:** Record per-qubit non-identity rates 1-P(I); use scalar p only when a named uniform channel defines it.

---

## Policy coverage

### 1. Which quaternary BP schedules should Phase 10 expose?

| Option | Description | Selected |
|--------|-------------|----------|
| Flooding and source-defined serial | Expose both source-backed schedules. | ✓ |
| Flooding only | Expose flooding alone in Phase 10. | |
| Other | Free-form preference. | |

**User’s choice:** Flooding and source-defined serial scheduling.

### 2. Should Phase 10 include source-defined normalization and offset transforms for quaternary check messages?

| Option | Description | Selected |
|--------|-------------|----------|
| Include both | Add both quaternary check-message transforms. | ✓ |
| Baseline messages only | Retain baseline check messages only. | |
| Other | Free-form preference. | |

**User’s choice:** Include both as declared quaternary policies with equations and compatibility checks.

### 3. Should MBP4 be part of Phase 10?

| Option | Description | Selected |
|--------|-------------|----------|
| Include MBP4 after Q-BPGD | Implement distinct MBP4 after required Q-BPGD. | ✓ |
| Defer MBP4 | Defer MBP4 beyond Phase 10. | |
| Other | Free-form preference. | |

**User’s choice:** Include MBP4 after required Q-BPGD as a distinct source-defined quaternary recurrence.

### 4. May individually source-backed quaternary policies be composed when the combination is unpublished?

| Option | Description | Selected |
|--------|-------------|----------|
| Allow after compatibility checks | Admit qualified unpublished combinations as labeled adaptations. | ✓ |
| Only published combinations | Admit only complete combinations described by papers. | |
| Other | Free-form preference. | |

**User’s choice:** Yes after mathematical and lifecycle compatibility checks; label the composition a canonical adaptation and declare order and semantics.

### 5. What scope of affine subcode ensemble decoding should Phase 10 implement?

| Option | Description | Selected |
|--------|-------------|----------|
| Full paper method | Implement splitter paths, virtual syndromes, selection, and overcomplete checks. | ✓ |
| Core affine ensemble first | Implement splitter paths now and overcomplete checks later. | |
| Other | Free-form preference. | |

**User’s choice:** Full paper aSCED including splitter paths, virtual syndromes, source candidate selection, and overcomplete-check option.

### 6. Should aSCED run on general stabilizer codes in Phase 10?

| Option | Description | Selected |
|--------|-------------|----------|
| Source-backed CSS first | Use the source-backed CSS construction; reject non-CSS aSCED. | ✓ |
| General stabilizer aSCED now | Derive and qualify a general stabilizer extension now. | |
| Other | Free-form preference. | |

**User’s choice:** Implement source-backed CSS aSCED first; reject non-CSS aSCED until a separate derivation and qualification.

### 7. How should the authors public aSCED repository be used?

| Option | Description | Selected |
|--------|-------------|----------|
| Executable reference and source guide | Pin and execute the author code as a separate native reference. | ✓ |
| Source guide only | Use author code only to study algorithm semantics. | |
| Other | Free-form preference. | |

**User’s choice:** Pin and execute it as a bounded native reference while independently implementing the canonical policy composition; keep identities and evidence separate.

### 8. What Phase 10 aSCED evidence is required?

| Option | Description | Selected |
|--------|-------------|----------|
| Bounded matched run | Run a bounded, shot-matched, unassessed comparison with path evidence. | ✓ |
| Deterministic fixtures only | Use deterministic fixtures only in Phase 10. | |
| Other | Free-form preference. | |

**User’s choice:** A bounded matched Pauli-sample run of canonical aSCED and standalone BP4, with qualified native reference, per-path work, and unassessed status; no curve reproduction claim.

---

## Q-BPGD ambiguities

### 1. What happens to BP edge messages between Q-BPGD rounds?

| Option | Description | Selected |
|--------|-------------|----------|
| Continue committed messages | Carry committed BP messages into the next decimation round. | ✓ |
| Restart messages each round | Reinitialize BP messages at each round. | |
| Other | Free-form preference. | |

**User’s choice:** Continue committed BP messages across rounds while changing the selected prior; record this as a canonical interpretation pending source-code qualification.

### 2. How are the papers fixation weights mapped to probabilities?

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve the papers ratios | Keep literal weights and normalize all entries by their common sum. | ✓ |
| Use normalized fixation weights | Change the leading weight to 1-3epsilon. | |
| Other | Free-form preference. | |

**User’s choice:** Preserve literal source weights (1-epsilon, epsilon, epsilon, epsilon), record them, and divide by their common sum for the probability API; do not substitute 1-3epsilon.

### 3. How are Q-BPGD equal-score ties resolved?

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed order | Choose lowest qubit index and I<X<Y<Z. | ✓ |
| Seeded random choice | Choose among ties with a recorded random seed. | |
| Other | Free-form preference. | |

**User’s choice:** Use lowest qubit index and Pauli order I<X<Y<Z, persist the interpretation for replay.

### 4. May Q-BPGD accept general declared joint priors?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, as a labeled extension | Permit general joint priors as a separately labeled adaptation. | ✓ |
| Depolarizing only | Use only the paper depolarizing setup. | |
| Other | Free-form preference. | |

**User’s choice:** Yes as a separately labeled canonical adaptation; the depolarizing setup remains the source-backed profile.

---

## Agent Discretion

- Exact CSS combined row order, quaternary saturation, schema version, smoothing options, bounded run sizes, and aSCED source-specific settings were left to research and planning, with explicit persistence and independent checks.

## Deferred Ideas

- General stabilizer aSCED requires a separate derivation; the source-backed Phase 10 profile is CSS-specific.
- Statistical quaternary reproduction remains in Phase 11 after Phase 8.
- The two keyword-matched pending todos retain their prior Phase 6 and paused Phase 7 assignments.
