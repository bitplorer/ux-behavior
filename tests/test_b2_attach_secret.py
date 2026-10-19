"""B2: attach() must not sign with the published dev secret.

Live script item3_behavior_b2_dev_secret.py. Part 2 (control() offline, empty
``data_cap``) is intended and pinned here. The forged-Cap HTTP check lives in
``test_b2_forged_cap.py`` (needs ux-channel).
"""

from __future__ import annotations

import builtins
import importlib.machinery
import importlib.util
import sys
import types

import pytest

from ux_behavior import Behavior, Component, action

PUBLIC_DEV_SECRET = "dev-secret-key-32chars-minimum!!!!"
_SECRET_ENV = ("UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL", "DEBUG")


class Vault(Component):
    id = "vault"
    wiped = False

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def _channel_stub() -> types.ModuleType:
    """Stand-in so secret checks still run when ux-channel is not installed."""
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
        def boot(asgi: object, config: object = None, path: str = "/ux-channel") -> object:
            raise RuntimeError("channel boot reached")

    module.Channel = Channel
    module.ChannelConfig = ChannelConfig
    return module


@pytest.fixture(autouse=True)
def _stub_channel_when_absent(monkeypatch: pytest.MonkeyPatch):
    """Secret-refusal tests import Channel before they raise.

    Without a package on the path that import returns None and never
    reaches the secret check. A present install is left alone.
    """
    if importlib.util.find_spec("ux_channel") is not None:
        yield
        return
    monkeypatch.setitem(sys.modules, "ux_channel", _channel_stub())
    yield


def test_control_offline_door_stays_open():
    """Part 2 of the live script: strict_control does not mint a Cap offline."""
    app = Behavior.boot(title="offline", strict_control=True)
    app.add(Vault)
    attrs = app.control("vault.wipe")
    assert attrs["data_action"] == "vault.wipe"
    assert attrs["data_cap"] == ""
    assert "CONTROL_OFFLINE" in app.diagnostics.summary()["codes"]


def test_attach_without_asgi_still_returns_none(clean_env: pytest.MonkeyPatch):
    assert Behavior.boot().attach(None) is None


def test_missing_channel_without_secret_returns_none(clean_env: pytest.MonkeyPatch):
    """A host with no ux-channel and no secret gets None, not a boot crash.

    The channel-import check has to run before secret resolution. Deleting
    that order makes this raise RuntimeError.
    """
    real_import = builtins.__import__

    def _block_channel(name, *args, **kwargs):
        if name == "ux_channel" or name.startswith("ux_channel."):
            raise ImportError("ux_channel blocked")
        return real_import(name, *args, **kwargs)

    clean_env.setattr(builtins, "__import__", _block_channel)
    clean_env.delitem(sys.modules, "ux_channel", raising=False)
    assert Behavior.boot().attach(object()) is None


def test_explicit_real_secret_is_not_refused(clean_env: pytest.MonkeyPatch):
    """A caller-supplied secret is not the public constant and is not rejected."""
    wire = Behavior.boot().attach(object(), secret="s" * 40)
    if wire is not None:
        assert wire.config.secret == "s" * 40
        assert wire.config.secret != PUBLIC_DEV_SECRET


def test_attach_without_secret_outside_dev_raises(clean_env: pytest.MonkeyPatch):
    with pytest.raises(RuntimeError, match="UX_CHANNEL_SECRET"):
        Behavior.boot().attach(object())


@pytest.mark.parametrize("raw", ["0", "false", "no", "off", "2", "maybe", " "])
def test_debug_falsey_requires_secret(clean_env: pytest.MonkeyPatch, raw: str):
    clean_env.setenv("DEBUG", raw)
    with pytest.raises(RuntimeError, match="UX_CHANNEL_SECRET"):
        Behavior.boot().attach(object())


@pytest.mark.parametrize("raw", ["1", "true", "yes", "on", " TRUE ", "Yes", "ON"])
def test_debug_truthy_allows_missing_secret(clean_env: pytest.MonkeyPatch, raw: str):
    """Dev signal is DEBUG in {1, true, yes, on} after strip + lower."""
    clean_env.setenv("DEBUG", raw)
    Behavior.boot().attach(object())


def test_explicit_public_constant_rejected_in_dev(clean_env: pytest.MonkeyPatch):
    clean_env.setenv("DEBUG", "1")
    with pytest.raises(RuntimeError, match="public dev secret"):
        Behavior.boot().attach(object(), secret=PUBLIC_DEV_SECRET)


def test_env_public_constant_rejected_outside_dev(clean_env: pytest.MonkeyPatch):
    clean_env.setenv("UX_CHANNEL_SECRET", PUBLIC_DEV_SECRET)
    with pytest.raises(RuntimeError, match="public dev secret"):
        Behavior.boot().attach(object())


def test_behavior_secret_env_public_constant_rejected(clean_env: pytest.MonkeyPatch):
    clean_env.setenv("UX_BEHAVIOR_SECRET", PUBLIC_DEV_SECRET)
    with pytest.raises(RuntimeError, match="public dev secret"):
        Behavior.boot().attach(object())


def test_redis_url_with_explicit_secret_is_accepted(clean_env: pytest.MonkeyPatch):
    """A configured secret still boots the Redis path. DEBUG does not matter."""
    clean_env.setenv("DEBUG", "1")
    clean_env.setenv("REDIS_URL", "redis://127.0.0.1:9/0")
    try:
        Behavior.boot().attach(object(), secret="s" * 40)
    except RuntimeError as exc:
        assert "REDIS_URL" not in str(exc)
        assert "public dev secret" not in str(exc)


def test_redis_url_in_dev_without_secret_raises(clean_env: pytest.MonkeyPatch):
    """REDIS_URL means more than one process, so DEBUG=1 is not a secret."""
    clean_env.setenv("DEBUG", "1")
    clean_env.setenv("REDIS_URL", "redis://127.0.0.1:9/0")
    with pytest.raises(RuntimeError, match="UX_CHANNEL_SECRET") as caught:
        Behavior.boot().attach(object())
    assert "REDIS_URL" in str(caught.value)


def test_redis_url_without_secret_outside_dev_raises(clean_env: pytest.MonkeyPatch):
    """REDIS_URL must not fall through to ChannelConfig.production(<constant>)."""
    clean_env.setenv("REDIS_URL", "redis://127.0.0.1:9/0")
    with pytest.raises(RuntimeError, match="UX_CHANNEL_SECRET"):
        Behavior.boot().attach(object())


def test_redis_url_with_public_constant_raises(clean_env: pytest.MonkeyPatch):
    clean_env.setenv("REDIS_URL", "redis://127.0.0.1:9/0")
    clean_env.setenv("UX_CHANNEL_SECRET", PUBLIC_DEV_SECRET)
    with pytest.raises(RuntimeError, match="public dev secret"):
        Behavior.boot().attach(object())
