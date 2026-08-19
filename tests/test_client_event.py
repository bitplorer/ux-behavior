"""wire.client_event — Host CustomEvent op, not public freeze."""

from __future__ import annotations

import ux_behavior
from ux_behavior.wire import Result, client_event


def test_not_on_frozen_public_surface():
    assert "client_event" not in ux_behavior.__all__
    assert not hasattr(ux_behavior, "client_event")


def test_shape_name_only():
    op = client_event("cart:added")
    assert op["op"] == "dispatch"
    assert op["name"] == "cart:added"
    assert op["bubbles"] is True
    assert "target" not in op
    assert "detail" not in op


def test_target_and_detail():
    op = client_event(
        "cart:added",
        target="#cart",
        detail={"sku": "tee"},
        bubbles=False,
    )
    assert op == {
        "op": "dispatch",
        "name": "cart:added",
        "target": "#cart",
        "detail": {"sku": "tee"},
        "bubbles": False,
    }


def test_empty_name_rejected():
    import pytest

    with pytest.raises(ValueError, match="name"):
        client_event("  ")


def test_folds_through_wire_result():
    ops = (
        Result()
        .morph("#cart", "<div/>")
        .op(client_event("cart:added", target="#cart", detail={"sku": "tee"}))
        .build()
    )
    assert ops[0]["op"] == "morph"
    assert ops[1]["op"] == "dispatch"
    assert ops[1]["name"] == "cart:added"
    assert ops[1]["target"] == "#cart"
