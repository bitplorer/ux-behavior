"""Trust is per caller: follow-ups inherit it, trust() never leaks across tasks."""
from __future__ import annotations

import asyncio

import pytest

from ux_behavior import AuthorityError, Behavior, Component, action, follow_up
from ux_behavior.root import _FRAMEWORK_TRUST


class Shop(Component):
    id = "shop"
    refunded = 0

    def render(self):
        return "<div id='shop'></div>"

    @action(caps=())
    def ask_refund(self):
        follow_up("approved", "shop.refund")
        return []

    @action(caps=("shop.refund",))
    def refund(self):
        self.refunded = int(self.refunded or 0) + 1


def _app():
    app = Behavior.boot(strict_caps=True)
    app.add(Shop)
    return app


def test_emit_does_not_grant_trust_to_untrusted_arming():
    app = _app()
    app.dispatch("shop.ask_refund")  # anonymous, public
    with pytest.raises(AuthorityError):
        app.emit("approved")
    assert app.get("shop").refunded == 0


@pytest.mark.asyncio
async def test_async_emit_does_not_grant_trust():
    app = _app()
    app.dispatch("shop.ask_refund")
    with pytest.raises(AuthorityError):
        await app.async_emit("approved")


def test_emit_inherits_trust_from_trusted_arming():
    app = _app()
    app.dispatch("shop.ask_refund", _trusted=_FRAMEWORK_TRUST)
    app.emit("approved")
    assert app.get("shop").refunded == 1


def test_emit_inherits_trust_from_trust_context():
    app = _app()
    with app.trust():
        app.dispatch("shop.ask_refund")
    app.emit("approved")
    assert app.get("shop").refunded == 1


def test_trust_does_not_flip_shared_strict_caps():
    app = _app()
    with app.trust():
        assert app.strict_caps is True
        app.dispatch("shop.refund")
    assert app.get("shop").refunded == 1


@pytest.mark.asyncio
async def test_trust_is_per_task_under_concurrency():
    app = _app()
    inside = asyncio.Event()
    release = asyncio.Event()

    async def trusted_task():
        with app.trust():
            inside.set()
            await release.wait()
            await app.async_dispatch("shop.refund")

    async def anonymous_task():
        await inside.wait()
        try:
            with pytest.raises(AuthorityError):
                await app.async_dispatch("shop.refund")
        finally:
            release.set()

    await asyncio.gather(trusted_task(), anonymous_task())
    assert app.get("shop").refunded == 1


def test_continuation_is_single_use():
    from ux_behavior import ContinuationError

    app = _app()
    app.dispatch("shop.ask_refund", _trusted=_FRAMEWORK_TRUST)
    app.emit("approved")
    with pytest.raises(ContinuationError):
        app.emit("approved")
    assert app.get("shop").refunded == 1
    assert "approved" not in app.continuations


@pytest.mark.asyncio
async def test_async_continuation_is_single_use():
    from ux_behavior import ContinuationError

    app = _app()
    app.dispatch("shop.ask_refund", _trusted=_FRAMEWORK_TRUST)
    await app.async_emit("approved")
    with pytest.raises(ContinuationError):
        await app.async_emit("approved")
    assert app.get("shop").refunded == 1
