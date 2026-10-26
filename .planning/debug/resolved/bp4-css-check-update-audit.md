---
status: resolved
trigger: "Check whether BP4 updates for X and Z stabilizers match the quantum decoding literature and the presentation pilot implementation."
created: 2026-10-25
updated: 2026-10-25
---

# BP4 X/Z stabilizer check-update audit

## Expected equations

For a CSS stabilizer row, the syndrome is the parity of single-qubit anticommutations. In the project's `I=0, X=1, Y=2, Z=3` encoding, an X check anticommutes with Y and Z errors, while a Z check anticommutes with X and Y errors. Thus `s_X=H_X e_Z` and `s_Z=H_Z e_X` over GF(2), where `e_X` and `e_Z` are the symplectic components of the Pauli error.

Each incoming four-state variable-to-check LLR vector is reduced for its own edge label `W` to

`lambda_W = log[(P(I)+P(W))/(sum of probabilities of the two Paulis anticommuting with W)]`.

For check `m` and target qubit `n`, the outgoing scalar commute-over-anticommute LLR is

`Delta_{m->n} = (-1)^{s_m} boxplus_{n' in N(m) excluding n} lambda_{S_{mn'}}(Gamma_{n'->m})`,

where `boxplus(a_1,...,a_k)=2 atanh(prod_i tanh(a_i/2))`. It adds to the LLRs for target Pauli states that anticommute with the **target** edge label. In particular, the incoming reduction uses each *neighbor's* edge label, not the target's label.

Primary references: [Kuo and Lai, *Exploiting degeneracy in belief propagation decoding of quantum codes*, Eq. (6)-(10)](https://www.nature.com/articles/s41534-022-00623-2) and [Poulin and Chung, *On the iterative decoding of sparse quantum codes*, single-qubit commutation table](https://www.rintonpress.com/xxqic8/qic-8-10/0987-1000.pdf).

## Code trace

- `run_reproduction.py` builds X-labeled rows from `H_X` and Z-labeled rows from `H_Z`; its syndrome is `(H_X e_Z, H_Z e_X)`.
- `policy_kernel.py` reduces every neighbor with its own edge label using `_commutation_llr(v2c[other], labels[other], bound)`, applies the observed syndrome sign, then adds the check message only to target Pauli states that anticommute with the target edge label.
- The compiled primitive `_anticommutes` implements the single-qubit Pauli table; `_commutation_llr` implements the two commute masses versus the two anticommute masses; `_boxplus_pair` implements the parity convolution in LLR form.

## Independent checks

`verify_spike.py` now enumerates all 192 target-edge cases for X/Z-labeled checks of degree 2, 3, and 4, for both syndrome bits, using independent four-state probability products and a literal anticommutation table. The compiled check LLRs agree within `1e-12` (maximum observed difference `6.66e-16`). Its existing structural checks compare the pilot graph edge for edge with the canonical CSS compilation and compare sampled syndromes. An additional 100 random Pauli assignments on double-Gross matched the direct CSS syndrome and BP4 graph parity.

Commands passed:

- `PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/verify_spike.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/canonical/quaternary/test_kernel.py -q` (`10 passed`)

## Resolution and limits

No X/Z check-label swap, syndrome sign inversion, or incorrect excluded-neighbor parity update was found. This supports the **mathematical check-update interpretation**, not equivalence to the slide's unspecified fixed-point implementation. The presentation excerpt does not state whether it rounds the commutation reduction, box-plus intermediate, check output, or variable beliefs, nor the exact flooding schedule, damping location, or tie rule. Those differences and code identity remain separate hypotheses for the performance gap. The pilot's `scale=4/16` message clipping is an adaptation until the source implementation or fuller method is available.
