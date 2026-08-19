"""Diagnostics catalog + production-safe Cap errors."""

from __future__ import annotations

import importlib.util

import pytest

from ux_behavior import AuthorityError, Behavior, Component, action
from ux_behavior.diagnostics import HINTS


class Orders(Component):
    id = "orders"

    def render(self):
        return ""

    @action(caps=("orders.write",))
    def place(self):
        return None


def test_default_cap_error_has_no_bypass_recipe():
    app = Behavior.boot()
    app.add(Orders)
    with pytest.raises(AuthorityError) as ei:
        app.dispatch("orders.place")
    msg = str(ei.value).lower()
    assert "trust" not in msg
    assert "_trusted" not in msg
    assert app.diagnostics.last_hint() == ""
    summary = app.diagnostics.summary()
    assert summary["developer_hints"] is False
    for ev in summary["events"]:
        assert ev["hint"] == ""
        assert ev["context"] == {}


def test_developer_hints_exposes_recipes():
    app = Behavior.boot(developer_hints=True)
    app.add(Orders)
    with pytest.raises(AuthorityError):
        app.dispatch("orders.place")
    hint = app.diagnostics.last_hint()
    assert hint
    assert "trust" in hint.lower() or "attach" in hint.lower()


def test_hints_cover_emitted_codes():
    emitted = {
        "ATTACH_ASYNC_HANDLER",
        "ATTACH_ASYNC_HANDLER_FAILED",
        "ATTACH_BOOT_FAILED",
        "ATTACH_DEV_SECRET",
        "ATTACH_IDEMPOTENT",
        "ATTACH_NO_ASGI",
        "ATTACH_OK",
        "CAP_REQUIRED",
        "CHANNEL_MISSING",
        "CLIENT_PLANE_PUSH_FAILED",
        "COMPONENT_REPLACE",
        "CONTINUATION_ARMED",
        "CONTINUATION_MISSING",
        "CONTROL_FALLBACK_OFFLINE",
        "CONTROL_MINTED",
        "CONTROL_MINT_FAILED",
        "CONTROL_NO_DISPATCH",
        "CONTROL_OFFLINE",
        "CORE_CHANNEL_ABSENT",
        "DISPATCH_EMPTY_ACTION",
        "DISPATCH_FAILED",
        "DRIVERS_FAILED",
        "DRIVERS_REPORT",
        "DRIVER_FAILED",
        "DRIVER_NO_USE",
        "PLANES_INSTALLED",
        "PLANES_INSTALL_FAILED",
        "PLANES_NO_CHANNEL_STATE",
        "PLANES_STATE_FAILED",
        "PLANE_CLIENT_FALLBACK",
        "PLANE_NO_BACKEND",
        "PLANE_SESSION_FALLBACK",
        "PREVIEW_OFF",
        "PREVIEW_ON",
        "REGION_EMPTY",
        "STAMP_REJECT",
        "TRUST_OFF",
        "TRUST_ON",
        "VALIDATION_FAILED",
    }
    missing = sorted(emitted - set(HINTS))
    assert missing == []


def test_strict_attach_missing_channel():
    if importlib.util.find_spec("ux_channel") is not None:
        pytest.skip("ux-channel installed")
    app = Behavior.boot(strict_attach=True)
    with pytest.raises(ImportError):
        app.attach(object())
