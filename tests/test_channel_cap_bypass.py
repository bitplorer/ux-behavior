"""Attaching a Channel must not turn off the in-process Cap check."""
from __future__ import annotations

import pytest

pytest.importorskip("ux_channel")
pytest.importorskip("fastapi")

from fastapi import FastAPI

from ux_behavior import AuthorityError, Behavior, Component, action


class Vault(Component):
    id = "vault"
    wiped = False

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True


def _attached():
    app = Behavior.boot(title="Bypass")
    app.add(Vault)
    app.region(lambda: "<div id='app.root'>ok</div>", uid="app.root")
    assert app.attach(FastAPI(), secret="s" * 40) is not None
    return app


def test_attached_untrusted_capped_dispatch_raises():
    app = _attached()
    with pytest.raises(AuthorityError):
        app.dispatch("vault.wipe")
    assert app.get("vault").wiped is False


@pytest.mark.asyncio
async def test_attached_untrusted_capped_async_dispatch_raises():
    app = _attached()
    with pytest.raises(AuthorityError):
        await app.async_dispatch("vault.wipe")


async def _channel_dispatch(app, *, cap: str | None):
    """Real Channel path: Intent on the registry -> ux_behavior.dispatch handler."""
    from ux_channel.protocol.types import Intent

    ch = app._wire
    args = {"ux_action": "vault.wipe"}
    return await ch.registry.async_dispatch(
        Intent(action="ux_behavior.dispatch", args=args, cap=cap)
    )


@pytest.mark.asyncio
async def test_real_channel_with_minted_cap_runs():
    app = _attached()
    ch = app._wire
    cap = ch.mint("ux_behavior.dispatch", {"ux_action": "vault.wipe"})
    result = await _channel_dispatch(app, cap=cap)
    assert getattr(result, "ok", None) is True, result
    assert app.get("vault").wiped is True


@pytest.mark.asyncio
async def test_real_channel_without_cap_is_refused():
    app = _attached()
    result = await _channel_dispatch(app, cap=None)
    assert getattr(result, "ok", None) is False
    assert app.get("vault").wiped is False
