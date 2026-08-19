"""Async actions, validation, preview, trust, client risk, dual emit."""

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


class Box(Component):
    id = "box"
    n = MorphState(0)
    theme = MorphState("system", backend="client", key="ui.theme")
    price = MorphState(0, backend="client", key="cart.price")

    def render(self):
        return f"<div>{self.n}</div>"

    @action(caps=())
    def set_n(self, n: int = 0):
        self.n = n
        return None

    @action(caps=())
    async def aset(self, n: int = 0):
        self.n = n
        return [notify("ok")]

    @action(caps=("x.write",))
    def secure(self):
        return [notify("s")]

    @action(caps=())
    def start(self):
        follow_up("done", "box.set_n", n=7)
        return [notify("go")]

    @action(caps=())
    async def astart(self):
        follow_up("adone", "box.aset", n=8)
        return [notify("ago")]


@pytest.mark.asyncio
async def test_async_dispatch_and_submit():
    app = Behavior.boot()
    app.add(Box)
    ops = await app.async_dispatch("box.aset", n=3)
    assert app.get("box").n == 3
    assert ops[0].pair == ("log", "append")
    await app.async_submit("box.aset", {"n": 4})
    assert app.get("box").n == 4


def test_sync_rejects_async_action():
    app = Behavior.boot()
    app.add(Box)
    with pytest.raises(TypeError, match="async"):
        app.dispatch("box.aset", n=1)


def test_validation_morph():
    app = Behavior.boot()
    app.add(Box)
    ops = app.dispatch("box.set_n", n="bad")  # type: ignore[arg-type]
    assert ops
    assert ops[0].pair == ("ui.dom", "morph")
    assert "error" in ops[0].payload["target"]


def test_preview_blocks_session():
    app = Behavior.boot()
    inst = app.add(Box)
    with app.preview():
        with pytest.raises(AuthorityError):
            inst.n = 9


def test_trust_context():
    app = Behavior.boot()
    app.add(Box)
    with pytest.raises(AuthorityError):
        app.dispatch("box.secure")
    with app.trust():
        assert app.dispatch("box.secure")


def test_client_risk():
    app = Behavior.boot()
    inst = app.add(Box)
    inst.theme = "dark"  # safe
    with pytest.raises(AuthorityError):
        inst.price = 10


def test_emit_sync():
    app = Behavior.boot()
    app.add(Box)
    app.dispatch("box.start")
    app.emit("done")
    assert app.get("box").n == 7


@pytest.mark.asyncio
async def test_async_emit():
    app = Behavior.boot()
    app.add(Box)
    await app.async_dispatch("box.astart")
    await app.async_emit("adone")
    assert app.get("box").n == 8
