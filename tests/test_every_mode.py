"""Every mode: sync/async entry × public/protected × trust/_trusted × emit/submit."""

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

    @action(caps=("demo.write",))
    def protected_set(self, n: int = 0):
        self.n = n
        return [notify(f"set {n}")]

    @action(caps=())
    def start_flow(self):
        follow_up("done", "demo.protected_set", n=9)
        return [notify("started")]

    @action(caps=())
    def start_async_flow(self):
        follow_up("adone", "demo.protected_async_set", n=11)
        return [notify("started async flow")]

    @action(caps=())
    def typed(self, n: int = 0):
        self.n = n
        return None

    @action(caps=())
    async def public_async_inc(self):
        self.n = int(self.n) + 10
        return None

    @action(caps=("demo.write",))
    async def protected_async_set(self, n: int = 0):
        self.n = n
        return [notify(f"async set {n}")]


def _app(**kw):
    app = Behavior.boot(**kw)
    app.add(Demo)
    return app


# ── Sync entry + sync action ──

def test_sync_public_dispatch_and_submit():
    app = _app()
    app.dispatch("demo.public_inc")
    assert app.get("demo").n == 1
    app.submit("demo.public_inc", {})
    assert app.get("demo").n == 2


def test_sync_protected_refuses():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        app.dispatch("demo.protected_set", n=1)
    with pytest.raises(AuthorityError):
        app.submit("demo.protected_set", {"n": 1})


def test_sync_protected_trust_and_trusted():
    app = _app(strict_caps=True)
    with app.trust():
        app.dispatch("demo.protected_set", n=3)
    assert app.get("demo").n == 3
    app.dispatch("demo.protected_set", n=4, _trusted=True)
    assert app.get("demo").n == 4
    app.submit("demo.protected_set", {"n": 5}, _trusted=True)
    assert app.get("demo").n == 5


def test_sync_emit_protected_continuation():
    app = _app(strict_caps=True)
    app.dispatch("demo.start_flow")
    app.emit("done")
    assert app.get("demo").n == 9


def test_sync_entry_rejects_async_action():
    app = _app()
    with pytest.raises(TypeError, match="async"):
        app.dispatch("demo.public_async_inc")
    with pytest.raises(TypeError, match="async"):
        app.submit("demo.public_async_inc", {})


def test_sync_validation_morph():
    app = _app()
    ops = app.dispatch("demo.typed", n="bad")  # type: ignore[arg-type]
    assert ops and "error" in ops[0].payload["target"]


# ── Async entry + sync action ──

@pytest.mark.asyncio
async def test_async_entry_sync_public():
    app = _app()
    await app.async_dispatch("demo.public_inc")
    assert app.get("demo").n == 1
    await app.async_submit("demo.public_inc", {})
    assert app.get("demo").n == 2


@pytest.mark.asyncio
async def test_async_entry_sync_protected_refuses():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        await app.async_dispatch("demo.protected_set", n=1)


@pytest.mark.asyncio
async def test_async_entry_sync_protected_trusted():
    app = _app(strict_caps=True)
    await app.async_dispatch("demo.protected_set", n=6, _trusted=True)
    assert app.get("demo").n == 6
    with app.trust():
        await app.async_dispatch("demo.protected_set", n=7)
    assert app.get("demo").n == 7


@pytest.mark.asyncio
async def test_async_emit_sync_protected_continuation():
    app = _app(strict_caps=True)
    app.dispatch("demo.start_flow")
    await app.async_emit("done")
    assert app.get("demo").n == 9


# ── Async entry + async action ──

@pytest.mark.asyncio
async def test_async_entry_async_public():
    app = _app()
    await app.async_dispatch("demo.public_async_inc")
    assert app.get("demo").n == 10
    await app.async_submit("demo.public_async_inc", {})
    assert app.get("demo").n == 20


@pytest.mark.asyncio
async def test_async_entry_async_protected_refuses():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        await app.async_dispatch("demo.protected_async_set", n=1)


@pytest.mark.asyncio
async def test_async_entry_async_protected_trusted_and_trust():
    app = _app(strict_caps=True)
    await app.async_dispatch("demo.protected_async_set", n=7, _trusted=True)
    assert app.get("demo").n == 7
    with app.trust():
        await app.async_dispatch("demo.protected_async_set", n=8)
    assert app.get("demo").n == 8


@pytest.mark.asyncio
async def test_async_emit_async_protected_continuation():
    app = _app(strict_caps=True)
    app.dispatch("demo.start_async_flow")
    await app.async_emit("adone")
    assert app.get("demo").n == 11


@pytest.mark.asyncio
async def test_async_validation_morph():
    app = _app()
    ops = await app.async_dispatch("demo.typed", n="bad")  # type: ignore[arg-type]
    assert ops and "error" in ops[0].payload["target"]


# ── Misc ──

def test_control_offline():
    app = _app()
    attrs = app.control(app.get("demo").public_inc)
    assert attrs["data_action"] == "demo.public_inc"
    assert attrs.get("data_cap", "") == ""


def test_strict_caps_false_sync():
    app = _app(strict_caps=False)
    app.dispatch("demo.protected_set", n=1)
    assert app.get("demo").n == 1


@pytest.mark.asyncio
async def test_strict_caps_false_async():
    app = _app(strict_caps=False)
    await app.async_dispatch("demo.protected_async_set", n=2)
    assert app.get("demo").n == 2


def test_preview_blocks_session_write():
    app = _app()
    with app.preview():
        with pytest.raises(AuthorityError):
            app.get("demo").n = 99


def test_public_still_works_after_protected_refuse():
    app = _app(strict_caps=True)
    with pytest.raises(AuthorityError):
        app.dispatch("demo.protected_set", n=1)
    app.dispatch("demo.public_inc")
    assert app.get("demo").n == 1
