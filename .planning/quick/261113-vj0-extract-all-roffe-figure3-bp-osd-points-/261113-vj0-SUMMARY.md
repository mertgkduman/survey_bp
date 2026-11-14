---
status: complete
implementation_commit: 04002e0
---

# All current-study BP-OSD source results tabulated

Added a separate Roffe Figure3 source comparison with all108 plotted BP+OSD-CS lambda60 ordinates, all109 ordinary-BP source rates and436 independently confirmed local measurements. The length450 code's unplotted p=.01 result is unavailable, not zero or an inferred upper bound. Every source point is matched to its drawn vertical error bar; source counts/work/confidence semantics remain unknown.

At X-only p=.02, paper BP+OSD-CS LER estimates for lengths162/242/338/450 are3.271e-5/5.781e-6/1.004e-6/1.946e-7. Our damped binary BP has.07273/.2151/.2299/.2326, about2,223/37,201/228,926/1,195,071 times higher. This is a large logical-performance benefit from OSD in the low-error regime, with additional elimination/search work. Q-BP is shown on depolarizing p=.03, so it remains contextual rather than a same-channel decoder ranking.

Saved full Markdown/CSV tables, source JSON, assessment and PNG/PDF in data/reproductions/roffe-2005-07016-osd-comparison. Included the paper's OSD-0/CS threshold summary and distinguished other figure settings. Added a link from the existing damping report and its generator.

Passed22 tests; figure visually inspected. All measured/catalog/source/frozen/kernel data are preserved; public104 curves/1073 points/12 codes/0 circuits unchanged. No OSD execution or new simulations. Source values are approximate vector ordinates, not local reproduction results. Phase11 counters and publication gates remain unchanged.
