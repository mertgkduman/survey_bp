# Phase 10 execution decisions — 2026-10-07

## GB46 aSCED splitter fixture

The pinned author generator uses unseeded `std::rand()` and does not retain its generated ordered `T` and `H_ext`. The planned `source_fixture_verified` receipt in the original Plans 10-10–10-12 therefore cannot be issued from the available source artifacts. The user selected a deterministic fixture explicitly labeled `canonical_adaptation` on 2026-10-07. Revised execution must bind that fixture to the original GB46 input, independently qualify its construction and `H_ext`, and keep source-backed algorithm components distinct from the run-level adaptation. The pinned overcomplete `M`/`H_oc` data may serve as source comparison fixtures only; a canonical overcomplete map must be constructed and qualified against the actual canonical `H_ext`.

## Native aSCED gate

The user sent `approved phase10 native spec 55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e` on 2026-10-07. The exact source specification remains `pending_human`: its license field is unresolved, and Plan 10-14 requires authoritative license or written permission in addition to digest approval. The user's subsequent statement, “author is communicated,” does not yet identify a grant, terms, or source. Clarification has been requested. No Plan 10-14 approval summary or native build/run may be issued until that evidence is reviewed and recorded.

The canonical adaptation decision does not authorize replacing the required native reference in Plans 10-15–10-16 or claiming source-faithful reproduction.
