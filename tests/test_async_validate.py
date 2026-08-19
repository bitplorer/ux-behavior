"""Async actions, validation morphs, preview, trust."""

from __future__ import annotations

import pytest

from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    MorphState,
    action,
    notify,
)


class Box(Component):
    id = "box"
    n = MorphState(0)

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


@pytest.mark.asyncio
async def test_async_dispatch():
    app = Behavior.boot()
    app.add(Box)
    ops = await app.async_dispatch("box.aset", n=3)
    assert app.get("box").n == 3
    assert ops[0].pair == ("log", "append")


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
