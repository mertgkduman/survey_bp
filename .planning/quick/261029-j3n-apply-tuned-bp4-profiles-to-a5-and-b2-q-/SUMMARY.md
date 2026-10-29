---
status: complete
date: 2026-10-29
---

# Tuned BP4 inside Q-BPGD complete

- Added a compiled float64 v2 Q-BPGD development path that preserves the canonical controller's ten-sweep block, original-syndrome check, deterministic four-state fixation, and committed V2C messages. The canonical replay function now accepts an explicit numerical profile while preserving its v1 default.
- Pinned the selected A5/B2 BP4 files and Q-BPGD settings in study-specific decoder files. Ran 1,000-shot pilots and separate 10,000-shot paired fixed samples at physical p=0.06; retained manifests, per-shot ledgers, summaries, and a report. This is a canonical adaptation, not source-qualified Figure 7 evidence.
- At 10,000 shots, A5 control/tuned failures were 12/7 with 8 rescues and 3 losses (exact paired p=0.2266); B2 was 2/2 with no discordant failures. Mean sweeps fell 13.445→11.561 and 14.409→12.191 respectively. Accuracy differences are unresolved.
- Verification: four development parity cases and existing Q-BPGD tests passed (10 focused tests); all four ledgers, manifests, source hashes, counts, and pair tallies verified.
