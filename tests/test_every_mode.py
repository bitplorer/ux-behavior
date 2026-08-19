"""Every authority / entry mode: offline public/protected, trust, trusted, emit, validation, async."""

from __future__ import annotations

import pytest

from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    MorphState,
    action,
    follow_up,
    notify,
)


class Demo(Component):
    id = "demo"
    n = MorphState(0)

    def render(self):
        return f"<div id='demo'>{self.n}</div>"

    @action(caps=())
    def public_inc(self):
        self.n = int(self.n) + 1
        return None

    @action(caps=())
    def public_notify(self):
        return [notify("hello")]

    @action(caps=("demo.write",))
    def protected_set(self, n: int = 0):
        self.n = n
        return [notify(f"set {n}")]

    @action(caps=())
    def start_flow(self):
        follow_up("done", "demo.protected_set", n=9)
        return [notify("started")]

    @action(caps=())
    def typed(self, n: int = 0):
        self.n = n
        return None

    @action(caps=())
    async def public_async(self):
        self.n = int(self.n) + 10
        return None


def _app(**kw):
    app = Behavior.boot(**kw)
    app.add(Demo)
    return app


def test_offline_public_inc_and_notify():
    app = _app()
    ops = app.dispatch("demo.public_inc")
    assert app.get("demo").n == 1
    assert ops[0].pair == ("ui.dom", "morph")
    ops = app.dispatch("demo.public_notify")
    assert ops[0].pair == ("log", "append")


def test_offline_control_no_cap():
    app = _app()
    attrs = app.control(app.get("demo").public_inc)
    assert attrs["data_action"] == "demo.public_inc"
    assert attrs.get("data_cap", "") == ""


def test_offline_protected_refuses():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        app.dispatch("demo.protected_set", n=1)


def test_offline_protected_trust_context():
    app = _app(strict_caps=True)
    with app.trust():
        app.dispatch("demo.protected_set", n=3)
    assert app.get("demo").n == 3


def test_offline_protected_trusted_kwarg():
    app = _app(strict_caps=True)
    app.dispatch("demo.protected_set", n=4, _trusted=True)
    assert app.get("demo").n == 4


def test_offline_strict_caps_false():
    app = _app(strict_caps=False)
    app.dispatch("demo.protected_set", n=5)
    assert app.get("demo").n == 5


def test_emit_runs_protected_continuation():
    app = _app(strict_caps=True)
    app.dispatch("demo.start_flow")
    app.emit("done")
    assert app.get("demo").n == 9


def test_validation_morph():
    app = _app()
    ops = app.dispatch("demo.typed", n="bad")  # type: ignore[arg-type]
    assert ops
    assert ops[0].pair == ("ui.dom", "morph")
    assert "error" in ops[0].payload["target"]


def test_sync_rejects_async_action():
    app = _app()
    with pytest.raises(TypeError, match="async"):
        app.dispatch("demo.public_async")


@pytest.mark.asyncio
async def test_async_dispatch_public():
    app = _app()
    await app.async_dispatch("demo.public_async")
    assert app.get("demo").n == 10


@pytest.mark.asyncio
async def test_async_dispatch_protected_trusted():
    app = _app(strict_caps=True)
    await app.async_dispatch("demo.protected_set", n=7, _trusted=True)
    assert app.get("demo").n == 7


def test_submit_helpers():
    app = _app()
    app.submit("demo.public_inc", {})
    assert app.get("demo").n == 1
    app.submit("demo.protected_set", {"n": 2}, _trusted=True)
    assert app.get("demo").n == 2


def test_preview_blocks_session_write():
    app = _app()
    with app.preview():
        with pytest.raises(AuthorityError):
            app.get("demo").n = 99


def test_attach_without_channel_returns_none():
    app = _app()
    # asgi object unused if channel missing
    ch = app.attach(object())
    # may be None if ux_channel not installed
    if ch is None:
        assert app.diagnostics.events  # CHANNEL_MISSING or similar recorded on attach path


def test_public_still_works_when_protected_refused():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        app.dispatch("demo.protected_set", n=1)
    app.dispatch("demo.public_inc")
    assert app.get("demo").n == 1
