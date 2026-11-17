---
id: 261117-htb
status: complete
campaign_status: unchanged
---

# No direct Relay crate reuse; origin of any adaptation remains unproven

Compared PriorTilt manifest/lock/core and retained history against pinned Relay v0.2.2 and current public main cdfdc996ce55582c4c431f8d8392bcce57175e36. PriorTilt builds its own priortilt_rs extension with no Relay package dependency. Its macro-generated flat-Vec/raw-pointer core differs from Relay's generic SparseBipartiteGraph/ndarray implementation. Check-node updates use prefix/suffix exclusive minima versus Relay's two-minimum method (four-lane optimization on current main). Variable updates share ordinary min-sum prefix/suffix arithmetic but have different storage/fusion. PriorTilt window-statistic prior offsets and Relay gamma-memory/relay legs are distinct policies.

The initial PriorTilt commit already contains the flat implementation; only one later commit changes its Rust file. No explicit derivation from Relay was found in the inspected release/history. This does not exclude an earlier port, consultation or substantial rewrite. An initial unspecified C++ reference does not identify origin, README "from scratch" describes resimulation, and licenses/history absence are not provenance proof. Similar observable-only Sinter projection is not evidence of code reuse.

Static assertions confirm manifest/lock absence of a Relay dependency, observed field/update structures and retained history. Full line-linked comparison and limits are in FINDINGS.md. No runtime or numerical equality/speed claim was tested; no simulations, frozen/source/kernel/public/model/gate/counter or existing output changes were made. Other collectors' pre-existing modified files remain outside staging. Native references and ten-CPU campaign continue unchanged.
