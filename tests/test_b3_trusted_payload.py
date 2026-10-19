"""B3: a ``_trusted`` key in payload data must not pass the Cap gate.

Live script item3_behavior_b3_trusted_kwarg.py. Trust is the private
sentinel ``_FRAMEWORK_TRUST`` (wire/attach.py passes it only after Channel
accepts the Cap). A bool, string, or int — including ``dispatch(**body)`` —
does not grant trust. ``submit(action, body)`` must not treat a body field
of that name as the flag.
"""

from __future__ import annotations

import logging

import pytest

from ux_behavior import AuthorityError, Behavior, Component, action, follow_up
from ux_behavior.root import _FRAMEWORK_TRUST
from ux_behavior.wire.attach import _payload_from


class Vault(Component):
    id = "vault"
    wiped = False

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True

    @action(caps=())
    def ask(self):
        follow_up("go", "vault.wipe")
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Vault)
    return app


def test_spread_body_trusted_bool_raises_and_warns(caplog: pytest.LogCaptureFixture):
    """dispatch(action, **request_body) must not treat a _trusted bool as trust."""
    app = _app()
    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        with pytest.raises(AuthorityError):
            app.dispatch("vault.wipe", **{"_trusted": True})
    assert app.get("vault").wiped is False
    assert any("ignoring _trusted" in record.message for record in caplog.records)


@pytest.mark.parametrize("flag", ["yes", 1])
def test_spread_body_trusted_truthy_values_do_not_grant_trust(
    caplog: pytest.LogCaptureFixture, flag: object
):
    app = _app()
    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        with pytest.raises(AuthorityError):
            app.dispatch("vault.wipe", **{"_trusted": flag})
    assert app.get("vault").wiped is False
    assert any("ignoring _trusted" in record.message for record in caplog.records)


def test_submit_body_trusted_raises():
    app = _app()
    with pytest.raises(AuthorityError):
        app.submit("vault.wipe", {"_trusted": True})
    assert app.get("vault").wiped is False


async def test_async_submit_body_trusted_raises():
    app = _app()
    with pytest.raises(AuthorityError):
        await app.async_submit("vault.wipe", {"_trusted": True})
    assert app.get("vault").wiped is False


def test_explicit_trusted_kwarg_still_runs():
    """Internal path: the sentinel the framework passes after Cap acceptance."""
    app = _app()
    app.dispatch("vault.wipe", _trusted=_FRAMEWORK_TRUST)
    assert app.get("vault").wiped is True


def test_submit_explicit_trusted_kwarg_still_runs():
    app = _app()
    app.submit("vault.wipe", {}, _trusted=_FRAMEWORK_TRUST)
    assert app.get("vault").wiped is True


async def test_async_dispatch_explicit_trusted_kwarg_still_runs():
    app = _app()
    await app.async_dispatch("vault.wipe", _trusted=_FRAMEWORK_TRUST)
    assert app.get("vault").wiped is True


def test_trust_context_still_runs():
    app = _app()
    with app.trust():
        app.dispatch("vault.wipe")
    assert app.get("vault").wiped is True


def test_untrusted_dispatch_still_raises():
    app = _app()
    with pytest.raises(AuthorityError):
        app.dispatch("vault.wipe")
    assert app.get("vault").wiped is False


def test_channel_payload_drops_trusted():
    class Ctx:
        form = {"_trusted": True, "name": "Ada"}

    payload = _payload_from(Ctx(), {"_trusted": True, "sku": "tee"})
    assert payload == {"sku": "tee", "name": "Ada"}


def test_emit_slot_trusted_does_not_grant_trust(caplog: pytest.LogCaptureFixture):
    app = _app()
    app.dispatch("vault.ask")
    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        with pytest.raises(AuthorityError):
            app.emit("go", _trusted=True)
    assert app.get("vault").wiped is False
    assert any("ignoring _trusted" in record.message for record in caplog.records)


async def test_async_emit_slot_trusted_does_not_grant_trust(
    caplog: pytest.LogCaptureFixture,
):
    """Twin of the sync emit test. Guards the async_emit payload strip.

    Deleting ``resolved = _without_payload_trust(resolved)`` in
    ``async_emit`` makes this raise TypeError (two values for ``_trusted``)
    instead of AuthorityError.
    """
    app = _app()
    app.dispatch("vault.ask")
    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        with pytest.raises(AuthorityError):
            await app.async_emit("go", _trusted=True)
    assert app.get("vault").wiped is False
    assert any("ignoring _trusted" in record.message for record in caplog.records)


def test_payload_from_args_trusted_is_logged(caplog: pytest.LogCaptureFixture):
    class Ctx:
        form: dict[str, object] = {}

    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        payload = _payload_from(Ctx(), {"_trusted": True, "sku": "tee"})
    assert payload == {"sku": "tee"}
    assert any("ignoring _trusted" in record.message for record in caplog.records)


def test_payload_from_form_trusted_is_logged(caplog: pytest.LogCaptureFixture):
    class Ctx:
        form = {"_trusted": True, "name": "Ada"}

    with caplog.at_level(logging.WARNING, logger="ux_behavior"):
        payload = _payload_from(Ctx(), {"sku": "tee"})
    assert payload == {"sku": "tee", "name": "Ada"}
    assert any("ignoring _trusted" in record.message for record in caplog.records)


async def test_async_plain_emit_logs_nothing(caplog: pytest.LogCaptureFixture):
    class Quiet(Component):
        id = "quiet"
        n = 0

        def render(self):
            return "<div id='quiet'></div>"

        @action(caps=())
        def arm(self):
            follow_up("go", "quiet.ping")
            return []

        @action(caps=())
        def ping(self):
            self.n = 1
            return []

    app = Behavior.boot()
    app.add(Quiet)
    app.dispatch("quiet.arm")
    with caplog.at_level(logging.DEBUG, logger="ux_behavior"):
        await app.async_emit("go")
    assert app.get("quiet").n == 1
    assert caplog.records == []


def test_plain_emit_logs_nothing(caplog: pytest.LogCaptureFixture):
    """A continuation slot with no ``_trusted`` key does not warn."""

    class Quiet(Component):
        id = "quiet"
        n = 0

        def render(self):
            return "<div id='quiet'></div>"

        @action(caps=())
        def arm(self):
            follow_up("go", "quiet.ping")
            return []

        @action(caps=())
        def ping(self):
            self.n = 1
            return []

    app = Behavior.boot()
    app.add(Quiet)
    app.dispatch("quiet.arm")
    with caplog.at_level(logging.DEBUG, logger="ux_behavior"):
        app.emit("go")
    assert app.get("quiet").n == 1
    assert caplog.records == []


def test_emit_keeps_trust_armed_by_framework_flag():
    app = _app()
    app.dispatch("vault.ask", _trusted=_FRAMEWORK_TRUST)
    app.emit("go", _trusted=False)
    assert app.get("vault").wiped is True
