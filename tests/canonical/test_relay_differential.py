"""Pinned-author Relay-BP differential test target."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Author v0.2.2 environment and behavior-neutral observer patch are not yet established.")
def test_pinned_author_relay_v022_matches_canonical_translation_on_tiny_fixture():
    """Reserved until the reviewed author environment is available in its isolated location."""


@pytest.mark.skip(reason="Author v0.2.2 instrumentation equivalence requires the external reviewed reference build.")
def test_observer_patch_preserves_unmodified_author_outputs():
    """Reserved differential behavior target for the checked source pin."""

