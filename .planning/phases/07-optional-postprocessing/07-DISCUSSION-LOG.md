# Phase 7: Optional Postprocessing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves alternatives considered.

**Date:** 2026-10-05
**Phase:** 07-Optional Postprocessing
**Areas discussed:** Fallback trigger and handoff, Method order and candidate choice, Literature TOML workflow, Phase 7 evidence view

---

## Todo routing

- **Folded into Phase 7:** Make literature TOML a native policy-file input. The user chose to carry its remaining fallback-related work into this phase.
- **Left with Phase 6:** Execute first CSS literature gate in the Phase 6 replan. The user chose not to move it into Phase 7.

## Fallback trigger and handoff

### 1. When a run has multiple BP attempts, when should optional processing start?

| Option | Description | Selected |
|---|---|---|
| After the whole BP/search run fails | Call fallback only if no original-valid BP candidate remains after the full search. | ✓ |
| After each failed BP attempt | Each failed branch or leg may invoke fallback before search finishes. |  |
| Declared trigger per composition | Policy chooses whole-search or attempt-level trigger. |  |

**User's choice:** After the whole BP/search run fails.

### 2. When several BP attempts fail, which reliability state should fallback receive?

| Option | Description | Selected |
|---|---|---|
| One declared best attempt | Pick one using fixed decoder-visible ranking. | ✓ |
| The final attempt | Use the last branch or leg to run. |  |
| Several attempts | Invoke fallback on several selected failures under a call budget. |  |

**User's choice:** One declared best attempt.

### 3. Should fallback process original CSS problem or selected attempt's transformed problem?

| Option | Description | Selected |
|---|---|---|
| Original problem | Transfer reliability into original coordinates. |  |
| Chosen attempt's working problem | Continue on transformed graph and lift the result. |  |
| Declared per method | Each method declares its problem handoff; every result is checked against original. | ✓ |

**User's choice:** Declared per method.

### 4. What if BP/search ends with execution error or has no usable reliability state?

| Option | Description | Selected |
|---|---|---|
| Skip fallback and record why | Keep error or missing-state status distinct from nonconvergence. | ✓ |
| Use last valid snapshot | Proceed if a complete earlier state exists. |  |
| Declare eligible terminal statuses | Configuration names each eligible failure status. |  |

**User's choice:** Skip fallback and record why.

---

## Method order and candidate choice

### 1. How should a decoder configuration use OSD, LSD, SI, and OTF?

| Option | Description | Selected |
|---|---|---|
| One method per configuration | Compare methods as separate matched arms. | ✓ |
| Declared sequence | Try enabled methods in order until success or cap. |  |
| Several methods independently | Run several on same handoff, then select candidate. |  |

**User's choice:** One method per configuration.

### 2. If a method produces several original-valid candidates, how should one be chosen?

| Option | Description | Selected |
|---|---|---|
| Common channel-prior score | Use one shared score and stable ties. |  |
| Method source rule | Preserve each method's published ranking. |  |
| Both by study type | Source ranking for faithful reproduction, common score for controlled comparison. | ✓ |

**User's choice:** Both by study type.

### 3. If fallback produces no original-valid candidate, what should decoder return?

| Option | Description | Selected |
|---|---|---|
| Retain BP-only output | Keep failed BP candidate as final and mark fallback unsuccessful. | ✓ |
| Return no candidate | Final output absent; BP output retained only for inspection. |  |
| Method declared failure output | Return a source-defined failure value with status. |  |

**User's choice:** Retain BP-only output.

### 4. If fallback reaches work limit after completing a valid candidate, is it eligible?

| Option | Description | Selected |
|---|---|---|
| Yes if fully reconstructed and validated | Keep completed original-valid candidate and capped work/status. | ✓ |
| No | Discard candidate if call later caps. |  |
| Follow source procedure | Eligibility depends on method's source rule. |  |

**User's choice:** Yes if fully reconstructed and validated.

---

## Literature TOML workflow

### 1. How should paper-linked BP-plus-fallback variant be saved?

| Option | Description | Selected |
|---|---|---|
| One runnable TOML per variant | Use existing seven-role file with postprocessing binding. | ✓ |
| Separate fallback TOML | Combine BP and fallback files at launch. |  |
| Study-level fallback settings | Keep BP policy file unchanged; study adds fallback. |  |

**User's choice:** One runnable TOML per variant.

### 2. How should a file identify BP and fallback from different sources?

| Option | Description | Selected |
|---|---|---|
| Separate source anchors per component | Record separate revisions and equation/algorithm anchors. | ✓ |
| One combined citation | Cite complete variant and explain borrowed component in prose. |  |
| Details only in PAPER.md | TOML links to companion record with component details. |  |

**User's choice:** Separate source anchors per component.

### 3. How should controlled study arms vary fallback while BP stays fixed?

| Option | Description | Selected |
|---|---|---|
| One complete TOML per arm | Repeat shared BP settings in each policy file. |  |
| One BP file plus study variants | Generate arms in study and save resolved manifests. |  |
| Support both | Complete paper variants and generated controlled arms with resolved manifests. | ✓ |

**User's choice:** Support both.

### 4. How should unresolved SI/OTF source variant and bounded runnable adaptation appear?

| Option | Description | Selected |
|---|---|---|
| Specification only | Keep non-runnable until source fully resolved. |  |
| Separate specification and adaptation | Retain spec plus distinctly labeled runnable adaptation after checks. | ✓ |
| One runnable file with warnings | Mix unresolved source details and executable settings. |  |

**User's choice:** Separate specification and adaptation.

---

## Phase 7 evidence view

### 1. What should be main way to inspect bounded fallback run?

| Option | Description | Selected |
|---|---|---|
| CLI report and verified ledger | Durable structured outcome and work tables. |  |
| Shot-by-shot notebook | Interactive inspection of handoff, fallback and candidates. |  |
| Both | Durable CLI/ledger plus compact shot-first notebook. | ✓ |

**User's choice:** Both.

### 2. Which arms should bounded demonstration put on same physical samples?

| Option | Description | Selected |
|---|---|---|
| BP-only, qualified canonical fallbacks, native references | Matched samples across all eligible arms; native composite separately identified. | ✓ |
| BP-only and canonical together, native separate | Native references verified apart from matched view. |  |
| One fallback at a time | Focused fixtures rather than multi-arm matched view. |  |

**User's choice:** BP-only, qualified canonical fallbacks, native references.

### 3. Which CSS code anchors matched view?

| Option | Description | Selected |
|---|---|---|
| B1 | Reuse small-study pattern; add method-specific deterministic fixtures. | ✓ |
| BB-144 | Use earlier native baseline artifact. |  |
| Method-specific codes | Within-code comparison only. |  |

**User's choice:** B1.

### 4. How show both no-fallback and fallback paths?

| Option | Description | Selected |
|---|---|---|
| Prespecified B1 samples plus fixtures | Retain every sampled shot and use separate deterministic path fixtures. | ✓ |
| Select B1 shots by BP outcome | Choose sample set after observing BP outcome. |  |
| Fixtures only | No sampled matched view. |  |

**User's choice:** Prespecified B1 samples plus fixtures.

---

## Agent discretion

- Exact failed-attempt ranking and tie rule; source-correct reliability conventions and standalone API choices; pinned SI/OTF variants; finite B1 budgets and display details, subject to CONTEXT.md decisions.

## Deferred ideas

- Published-curve statistical campaigns and CSS reproduction remain in Phases 8–9.
- Public policy-file voting remains assigned to Phase 9.
