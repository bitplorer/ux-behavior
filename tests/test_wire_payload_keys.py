"""Wire payloads named ``action`` and ``self`` follow the dispatch contract.

Entry-point parameters are positional-only, so those keys are caller data.
A key binds when the action names it. A key the signature does not name is
not passed into ``**kwargs``. ``self`` stays the component instance.
"""

from __future__ import annotations

import importlib.machinery
import inspect
import sys
import types

import pytest

from ux_behavior import Behavior, Component, action


class Gate(Component):
    id = "gate"
    got = None

    def render(self):
        return "<div id='gate'></div>"

    @action(caps=())
    def save(self, /, email: str = "", action: str = "", **extra):
        self.got = (self.id, email, action, extra.get("self", "absent"))
        return []


def _channel(*, reject_async: bool) -> types.ModuleType:
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
        handler = None

        @staticmethod
        def boot(asgi: object, config: object = None, path: str = "/ux-channel") -> "Channel":
            return Channel()

        def region(self, uid: str):
            def decorate(paint):
                return paint

            return decorate

        def on(self, name: str, refresh: object = None, idempotent: bool = False):
            def decorate(fn):
                if reject_async and inspect.iscoroutinefunction(fn):
                    raise TypeError("async handler rejected")
                self.handler = fn
                return fn

            return decorate

    module.Channel = Channel
    module.ChannelConfig = ChannelConfig
    return module


def _attach(monkeypatch: pytest.MonkeyPatch, *, reject_async: bool) -> Behavior:
    monkeypatch.setenv("UX_CHANNEL_SECRET", "s" * 40)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.setitem(sys.modules, "ux_channel", _channel(reject_async=reject_async))
    app = Behavior.boot()
    app.add(Gate)
    assert app.attach(object(), channel_planes=False) is not None
    return app


async def test_async_wire_binds_named_action_and_drops_self(monkeypatch: pytest.MonkeyPatch):
    app = _attach(monkeypatch, reject_async=False)
    await app._dispatch(
        None,
        ux_action="gate.save",
        email="ada@atelier.test",
        action="keep",
        self="intruder",
    )
    assert app.get("gate").got == ("gate", "ada@atelier.test", "keep", "absent")


def test_sync_wire_binds_named_action_and_drops_self(monkeypatch: pytest.MonkeyPatch):
    app = _attach(monkeypatch, reject_async=True)
    app._dispatch(
        None,
        ux_action="gate.save",
        email="ada@atelier.test",
        action="keep",
        self="intruder",
    )
    assert app.get("gate").got == ("gate", "ada@atelier.test", "keep", "absent")
