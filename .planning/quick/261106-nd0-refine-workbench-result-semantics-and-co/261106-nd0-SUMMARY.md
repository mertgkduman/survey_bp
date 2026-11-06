---
quick_id: 261106-nd0
status: complete
date: 2026-11-06
implementation_commit: dc39055
verification: passed
---

# Workbench result semantics and composable experiment builder

Delivered the requested v2 revision in `dc39055`.

## Result exploration

- Q-BP replaces BP4 in public decoder labels; historical API/profile identifiers remain intact. Names use commas, and both result and builder searches support prefix filtering and keyboard selection.
- Zero-failure bounds have error bars and are excluded from connecting paths. Depolarizing labels consistently use physical p with X/Y/Z each p/3. Mixed X-only/depolarizing comparisons convert depolarizing x coordinates to the component bit-flip rate automatically.
- Equivalent decoder evidence shares a view without seed/set/N legend splits. Original members and seeds remain in receipts and reproduction details. Exact reused data is deduplicated; known disjoint fixed-IID cohorts alone may pool. Curve view IDs stay stable when evidence is added.
- Restored three real circuit CPU-profile curves. Their omission was a catalog adapter gap, not clipping-based invalidation. The p=0.005, MS, T=8 results are explicitly local CPU mechanism/performance evidence; the older report repeats samples and is provenance only.
- Removed the three-qubit fixture from active public choices and replaced the terminal code-capacity example with BB72. Archived v1 and internal test artifacts remain intact.

## Experiment construction and execution

- Added BP and Q-BP baseline presets, searchable saved decoders, and rendered kernel/numerical-rule guides.
- Q-BPGD can compose SP/MS, damping, scaling/offset, resolution, and coefficient policies through its shared persistent-message recurrence. Fixation updates priors without resetting committed messages. The frozen no-policy path remains unchanged.
- Registered code selection loads exact generated matrix previews. Custom matrices remain editable with shared algebra/compatibility validation.
- Circuit sweeps replace only matching noisy-gate probability arguments, preserve tags/targets/coordinates/repeats, generate a Stim input per rate, and validate each resulting DEM/adapter before execution.
- Uniform or separately configured per-point limits support shots, total failures, Type I and Type II, with first-condition or all-target stopping. Empty means unlimited and all-empty is rejected. All-target shots is a target, not a hard ceiling.
- Circuit Type I/II explicitly partitions observable failures without/with detector fit. Legacy total ceilings, deterministic Stim shot-prefix traversal, mixed per-point uncertainty, and old adaptive result imports are validated.

## Verification and delivery

- 144 tests passed; 22 browser workflow groups passed without browser errors.
- Downloaded Q-BPGD and multi-rate Stim packages ran locally on small fixtures and their result imports were verified.
- Desktop/mobile layouts, keyboard controls, exact settings/CSV exports, retired-profile exclusions, and archived-v1 package validation passed.
- Independent scientific review resolved the initial contract blockers. No new expensive performance campaign was launched.

See `261106-nd0-VERIFICATION.md`, `261106-nd0-SCIENTIFIC-REVIEW.md`, and `261106-nd0-verification.json` for commands, evidence, and explicit limits. Documentation: `docs/research-interface.md`.

Local preview: `http://127.0.0.1:8765/web/research/`. The preview is a repository-local static server; simulations execute locally after download.
