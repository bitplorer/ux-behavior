"""One-call verified dispatch for a second wire.

The helper passes the private sentinel for that call only. A task created
while the action runs does not inherit the grant. The sentinel stays off
the public surface.
"""

from __future__ import annotations

import asyncio

import pytest

from ux_behavior import AuthorityError, Behavior, Component, action


class Vault(Component):
    id = "vault"
    wiped = False
    child_ran = False
    task: asyncio.Task | None = None

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True
        return []

    @action(caps=("vault.wipe",))
    async def wipe_async(self):
        self.wiped = True
        return []

    @action(caps=("vault.wipe",))
    def spawn(self):
        self.wiped = True
        app = self._behavior

        async def later():
            await app.async_dispatch("vault.child")

        self.task = asyncio.create_task(later())
        return []

    @action(caps=("vault.wipe",))
    async def spawn_async(self):
        self.wiped = True
        app = self._behavior

        async def later():
            await app.async_dispatch("vault.child")

        self.task = asyncio.create_task(later())
        return []

    @action(caps=("vault.wipe",))
    def child(self):
        self.child_ran = True
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Vault)
    return app


def test_dispatch_verified_grants_trust_for_that_call():
    app = _app()
    app.dispatch_verified("vault.wipe", {})
    assert app.get("vault").wiped is True


async def test_async_dispatch_verified_grants_trust_for_that_call():
    app = _app()
    await app.async_dispatch_verified("vault.wipe_async", {})
    assert app.get("vault").wiped is True


def test_dispatch_verified_ignores_payload_trusted():
    app = _app()
    app.dispatch_verified("vault.wipe", {"_trusted": False})
    assert app.get("vault").wiped is True


async def test_task_spawned_inside_dispatch_verified_is_not_trusted():
    app = _app()
    app.dispatch_verified("vault.spawn", {})
    assert app.get("vault").wiped is True
    with pytest.raises(AuthorityError):
        await app.get("vault").task
    assert app.get("vault").child_ran is False


async def test_task_spawned_inside_async_dispatch_verified_is_not_trusted():
    app = _app()
    await app.async_dispatch_verified("vault.spawn_async", {})
    assert app.get("vault").wiped is True
    with pytest.raises(AuthorityError):
        await app.get("vault").task
    assert app.get("vault").child_ran is False


def test_verified_docstring_is_for_framework_after_cap_check():
    phrase = (
        "only for framework code after Channel or an equivalent check "
        "has verified the Cap"
    )
    assert phrase in Behavior.dispatch_verified.__doc__
    assert phrase in Behavior.async_dispatch_verified.__doc__


def test_sentinel_stays_private():
    import ux_behavior

    assert "_FRAMEWORK_TRUST" not in ux_behavior.__all__
    assert not hasattr(ux_behavior, "_FRAMEWORK_TRUST")
    assert "dispatch_verified" in ux_behavior.__all__
    assert "async_dispatch_verified" in ux_behavior.__all__
