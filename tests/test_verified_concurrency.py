"""A verified call must not leave trust for any other call.

These pins fail a shared global that is set for the duration of
``dispatch_verified`` and cleared in ``finally``, and they fail a reset
that is skipped on return, on raise, or on cancel.
"""

from __future__ import annotations

import asyncio

import pytest

from ux_behavior import AuthorityError, Behavior, Component, action


class Vault(Component):
    id = "vault"
    wiped = False
    plain_ran = False
    entered: asyncio.Event
    release: asyncio.Event

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True
        return []

    @action(caps=("vault.wipe",))
    def plain(self):
        self.plain_ran = True
        return []

    @action(caps=("vault.wipe",))
    def boom(self):
        raise RuntimeError("boom")

    @action(caps=("vault.wipe",))
    async def slow(self):
        self.entered.set()
        await self.release.wait()
        self.wiped = True
        return []


def _app() -> tuple[Behavior, Vault]:
    app = Behavior.boot()
    app.add(Vault)
    inst = app.get("vault")
    inst.entered = asyncio.Event()
    inst.release = asyncio.Event()
    return app, inst


async def test_slow_verified_call_does_not_trust_a_concurrent_plain_call():
    app, inst = _app()
    verified = asyncio.create_task(app.async_dispatch_verified("vault.slow", {}))
    await inst.entered.wait()
    with pytest.raises(AuthorityError):
        app.dispatch("vault.plain")
    assert inst.plain_ran is False
    inst.release.set()
    await verified
    assert inst.wiped is True


def test_plain_call_after_verified_call_raises():
    app, inst = _app()
    app.dispatch_verified("vault.wipe", {})
    assert inst.wiped is True
    with pytest.raises(AuthorityError):
        app.dispatch("vault.plain")
    assert inst.plain_ran is False


def test_plain_call_after_verified_call_raises_on_error():
    app, inst = _app()
    with pytest.raises(RuntimeError, match="boom"):
        app.dispatch_verified("vault.boom", {})
    with pytest.raises(AuthorityError):
        app.dispatch("vault.plain")
    assert inst.plain_ran is False


async def test_plain_call_after_cancelled_verified_call_raises():
    app, inst = _app()
    verified = asyncio.create_task(app.async_dispatch_verified("vault.slow", {}))
    await inst.entered.wait()
    verified.cancel()
    with pytest.raises(asyncio.CancelledError):
        await verified
    with pytest.raises(AuthorityError):
        app.dispatch("vault.plain")
    assert inst.plain_ran is False


async def test_plain_call_after_same_task_timeout_raises():
    """A timeout in this task must not leave the next plain call trusted."""
    app, inst = _app()
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.05):
            await app.async_dispatch_verified("vault.slow", {})
    with pytest.raises(AuthorityError):
        app.dispatch("vault.plain")
    assert inst.plain_ran is False
