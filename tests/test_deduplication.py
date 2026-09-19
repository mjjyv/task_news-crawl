"""Unit tests for Deduplication engine (Local and Redis fallback)."""

import pytest
from crawler.deduplicator import LocalDeduplicator, get_deduplicator


def test_local_deduplicator_lifecycle():
    dedup = LocalDeduplicator()
    assert dedup.count() == 0

    # First time seeing ID 100
    assert not dedup.is_seen(100)
    assert dedup.mark_seen(100) is True
    assert dedup.is_seen(100) is True
    assert dedup.count() == 1

    # Second time seeing ID 100
    assert dedup.mark_seen(100) is False
    assert dedup.count() == 1

    # Filter unseen
    input_ids = [100, 101, 102, 100, 101]
    unseen = dedup.filter_unseen(input_ids)
    assert set(unseen) == {101, 102}

    # Clear
    dedup.clear()
    assert dedup.count() == 0
    assert not dedup.is_seen(100)


def test_get_deduplicator_fallback():
    # If redis isn't running, it should fallback to LocalDeduplicator seamlessly
    dedup = get_deduplicator(prefer_redis=True)
    assert dedup is not None
    # Verify basic interface functions without error
    assert not dedup.is_seen(999999)
