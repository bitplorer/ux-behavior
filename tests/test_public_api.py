"""Public surface is small and intentional."""

from __future__ import annotations

import ux_behavior


def test_all_is_frozen_and_small():
    names = set(ux_behavior.__all__)
    assert "Behavior" in names
    assert "Component" in names
    assert "action" in names
    assert "update" in names
    assert "compose" not in names
    assert "lower" not in names
    assert "adapter" not in names
    assert "client_event" not in names
    assert "Result" not in names
