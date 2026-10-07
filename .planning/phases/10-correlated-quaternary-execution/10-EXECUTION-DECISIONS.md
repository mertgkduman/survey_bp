# Phase 10 execution decisions — 2026-10-07

## GB46 aSCED splitter fixture

The pinned author generator uses unseeded `std::rand()` and does not retain its generated ordered `T` and `H_ext`. The planned `source_fixture_verified` receipt in the original Plans 10-10–10-12 therefore cannot be issued from the available source artifacts. The user selected a deterministic fixture explicitly labeled `canonical_adaptation` on 2026-10-07. Its pinned original input is `Codes/GB_46_2/GB_46_2_H_44.alist` at commit `816772071486615dfc7d71d1e15df597edc58a26`, raw SHA-256 `4bd60bc22ccda388780ad2ad2a29b63143b3f024e599e57ef5bcb983f51cb9b2`. This identity is specified separately from the digest-approved native proposal, which does not list this matrix. Revised execution must bind that fixture to the original GB46 input, independently qualify its construction and `H_ext`, and keep source-backed algorithm components distinct from the run-level adaptation. The pinned overcomplete `M`/`H_oc` data may serve as source comparison fixtures only; a canonical overcomplete map must be constructed and qualified against the actual canonical `H_ext`.

## Native aSCED gate

The user sent `approved phase10 native spec 55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e` on 2026-10-07. The user then clarified on 2026-10-07 that the author is a collaborator and has given permission verbally. Plan 10-14 records this user-attested verbal author permission as sufficient for the exact bounded isolated build and run, while explicitly recording that no written permission text or repository license was supplied or located. This is a user-approved deviation from the plan's request for written evidence. The digest-bound source spec remains byte-for-byte unchanged; its `pending_human` field describes the pre-decision proposal, with `10-14-SUMMARY.md` serving as the decision record.

The canonical adaptation decision does not authorize replacing the required native reference in Plans 10-15–10-16 or claiming source-faithful reproduction.
