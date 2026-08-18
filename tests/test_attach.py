"""wire.attach — soft when Channel missing."""

from __future__ import annotations

from ux_behavior import Behavior
from ux_behavior.wire import attach, attach_info, present, probe


def test_probe_keys():
    p = probe()
    assert "ux_dom" in p
    assert "ux_channel" in p


def test_attach_without_asgi_returns_none():
    app = Behavior.boot(title="Shop")
    assert attach(app, None) is None


def test_attach_info():
    app = Behavior.boot(title="Shop")
    info = attach_info(app)
    assert info["title"] == "Shop"
    assert info["attached"] is False
    assert isinstance(present(), bool)
