"""Domain stamp + submit_outcome."""

from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, action, submit_outcome
from ux_behavior.ops import Op
from ux_behavior.wire.attach import attach_info, probe


def test_default_stamp_allows_s_pairs():
    app = Behavior.boot()
    assert ("ui.dom", "morph") in app.stamp
    assert ("log", "append") in app.stamp
    assert ("nav", "push") in app.stamp


def test_product_domain_stamps_pairs():
    app = Behavior.boot()
    app.domain("orders", "1", [("orders", "create")])
    assert ("orders", "create") in app.stamp
    assert "orders" in app.domains.names


def test_dispatch_rejects_unstamped_pair():
    class Bad(Component):
        id = "x"

        def render(self):
            return ""

        @action(caps=())
        def boom(self):
            return [Op("secret", "leak", {})]

    app = Behavior.boot()
    app.add(Bad)
    with pytest.raises(PermissionError, match="not on the session stamp"):
        app.dispatch("x.boom")


def test_submit_outcome():
    ops = submit_outcome("#form", "<ok/>", message="Saved")
    assert len(ops) == 2
    assert ops[0].pair == ("ui.dom", "morph")
    assert ops[1].pair == ("log", "append")


def test_attach_probe():
    info = attach_info(Behavior.boot(title="Shop"))
    assert info["title"] == "Shop"
    assert "ux_channel" in info["cores"]
    assert isinstance(probe(), dict)
