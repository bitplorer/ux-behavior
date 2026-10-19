"""Sync dispatch handler when Channel rejects an async ``on`` callback.

Covers the fallback in ``wire/attach.py`` that registers a sync handler
and still passes the private sentinel after Channel has accepted the Cap.
"""

from __future__ import annotations

import importlib.machinery
import inspect
import sys
import types

import pytest

from ux_behavior import Behavior, Component, action


class Vault(Component):
    id = "vault"
    wiped = False

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True
        return []


def _channel_that_rejects_async() -> types.ModuleType:
    module = types.ModuleType("ux_channel")
    module.__spec__ = importlib.machinery.ModuleSpec("ux_channel", loader=None)

    class _Config:
        def __init__(self, secret: str) -> None:
            self.secret = secret

        def with_redis(self, url: str) -> "_Config":
            return self

    class ChannelConfig:
        @staticmethod
        def development(secret: str = "", allow_memory_stores: bool = True) -> _Config:
            return _Config(secret)

        @staticmethod
        def production(secret: str) -> _Config:
            return _Config(secret)

    class Channel:
        @staticmethod
        def boot(asgi: object, config: object = None, path: str = "/ux-channel") -> "Channel":
            return Channel()

        def region(self, uid: str):
            def decorate(paint):
                return paint

            return decorate

        def on(self, name: str, refresh: object = None, idempotent: bool = False):
            def decorate(fn):
                if inspect.iscoroutinefunction(fn):
                    raise TypeError("async handler rejected")
                self.handler = fn
                return fn

            return decorate

    module.Channel = Channel
    module.ChannelConfig = ChannelConfig
    return module


def test_sync_fallback_dispatches_with_framework_trust(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("UX_CHANNEL_SECRET", "s" * 40)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.setitem(sys.modules, "ux_channel", _channel_that_rejects_async())

    app = Behavior.boot()
    app.add(Vault)
    wire = app.attach(object(), channel_planes=False)
    assert wire is not None
    assert "ATTACH_ASYNC_HANDLER_FAILED" in app.diagnostics.summary()["codes"]
    assert not inspect.iscoroutinefunction(app._dispatch)

    app._dispatch(None, ux_action="vault.wipe")
    assert app.get("vault").wiped is True

    app._dispatch(None, ux_action="")
    assert "DISPATCH_EMPTY_ACTION" in app.diagnostics.summary()["codes"]
