# Phase 1 source-artifact decision record

## D-03 inventory

The inventory in `data/evidence/code-inventory.json` keeps three distinct leads.
`B1 [[882,24,18<=d<=24]]` is a **lifted-product** code in the impulse
paper (v1, Figure 5); it must not be conflated with the BPGD paper's C2.
`C2 [[1922,50,16]]` is the **hypergraph-product** code named by the BPGD
paper (v2, Figure 5).  Gross/BB-144 is a bivariate-bicycle lead related at
the parameter level to impulse Figure 6 and to the Bravyi construction paper.

Each lead records its paper relation separately from its executable source
identity. A parameter tuple or family name never establishes matrix ordering,
logical-basis row ordering, or source-faithful equivalence.

## Conditional ranking before the source probe

1. **Gross/BB-144** was the conditional first choice because Bravyi's public
   repository supplied a full commit, `decoder_setup.py`, and a stated
   `bposd.css.css_code` logical-extraction path.
2. **B1 lifted product** had paper evidence but no verified original matrix or
   ordered-logical artifact.
3. **C2 HGP** had an explicit family relation but no pinned matrix seed,
   product ordering, or ordered-logical artifact.

The ranking was only a reason to probe Gross first. It was not a selection.

## Gross pinned-source probe

The checked repository is
`https://github.com/sbravyi/BivariateBicycleCodes` at
`fa77e3333d3ec44c79d8f914dd24c040d1da471b` (2024-04-29). Its actual
`decoder_setup.py` SHA-256 is
`e919e1830b88468c5d257c0119656576a7999f92743dfeccd389a967524b3d2c`.
The reviewed active parameters are `ell=12`, `m=6`,
`a=(3,1,2)`, and `b=(3,1,2)`, with source ordering
`Hx=[A|B]`, `Hz=[B^T|A^T]`.

`tools/freeze_css_source.py` reads that commit and reconstructs only this
matrix recipe; it does not import the source program or run its circuit/data
generation side effects. In the approved `.venv`, independent GF(2)
calculation produced Hx and Hz shapes `(72,144)`, ranks `66` and `66`,
`k=12`, and zero entries in `Hx Hz^T`. The approved
`bposd==2.1` logical provider (`bposd/css.py` SHA-256
`d1e0c238d81c9b023bffa7bd355cfe305f8da3a6233a0af2edc1187f4807d6b1`)
also reported `K=12` and emitted 12 Lx and 12 Lz rows.

The probe establishes Gross as the conditional first choice. Its provider
rows are still not a selected artifact: Task 2 must record their actual row
fingerprints, normalize the ordered Lz partners explicitly, and independently
validate the resulting ordered paired basis.

## Final D-04 decision and rejected candidates

**Gross/BB-144 is conditionally selected for Task 2, not yet promoted as a
verified artifact.** B1 is rejected for this pilot because its exact matrix
source and ordered logical rows are absent. C2 is rejected for this pilot
because its source matrices, HGP construction ordering, and ordered logical
rows are absent.

Task 2 may create the selected artifact only if exact Gross rows regenerate
from the cited commit, the source-provider row fingerprints are retained, and
project-owned GF(2) pairing and quotient checks pass. A parameter label or
guessed source identity cannot substitute for this gate.

## Relation to the Phase 1 native pilot

No source-faithful reproduction or selected-code pilot is authorized by this
record. The existing project-owned three-qubit run remains a disclosed pilot
adaptation and does not fill this source-artifact gate.
