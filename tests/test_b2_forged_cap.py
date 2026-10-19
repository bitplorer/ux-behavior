"""B2 live HTTP: a Cap signed with the published dev constant is rejected.

Same shape as item3_behavior_b2_dev_secret.py. The victim is ``attach()``
with no secret and DEBUG=1 (the dev path). Outside dev, that call raises;
see ``test_b2_attach_secret.py``. Skipped when ux-channel is not installed.
"""

from __future__ import annotations

import json
import socket
import threading
import time

import pytest

pytest.importorskip("ux_channel")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("uvicorn")

import httpx
import uvicorn
from fastapi import FastAPI
from ux_channel import Channel, ChannelConfig

from ux_behavior import Behavior, Component, action

PUBLIC_DEV_SECRET = "dev-secret-key-32chars-minimum!!!!"
_HDR = {
    "Content-Type": "application/ux-channel+json",
    "Accept": "application/ux-channel+json",
    "X-Channel": "1",
}


class Vault(Component):
    id = "vault"
    wiped = False

    def render(self):
        return "<div id='vault'></div>"

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True


class _Served:
    def __init__(self, app: FastAPI) -> None:
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        self.server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(200):
            if self.server.started:
                break
            time.sleep(0.05)
        if not self.server.started:
            raise RuntimeError("victim server did not start")
        self.base = f"http://127.0.0.1:{port}"

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)


def _clear(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL"):
        monkeypatch.delenv(key, raising=False)


def _post(client: httpx.Client, cap: str | None) -> httpx.Response:
    body: dict[str, object] = {
        "action": "ux_behavior.dispatch",
        "args": {"ux_action": "vault.wipe"},
    }
    if cap is not None:
        body["cap"] = cap
    return client.post("/ux-channel/action", headers=_HDR, content=json.dumps(body))


def test_dev_forged_cap_signed_with_public_constant_is_401(
    monkeypatch: pytest.MonkeyPatch,
):
    _clear(monkeypatch)
    monkeypatch.setenv("DEBUG", "1")

    asgi = FastAPI()
    behavior = Behavior.boot(title="Victim")
    behavior.add(Vault)
    behavior.region(lambda: "<div id='app.root'>ok</div>", uid="app.root")
    wire = behavior.attach(asgi)
    assert wire is not None
    assert wire.config.secret != PUBLIC_DEV_SECRET

    attacker = Channel.boot(
        FastAPI(),
        config=ChannelConfig.development(
            secret=PUBLIC_DEV_SECRET, allow_memory_stores=True
        ),
    )
    forged = attacker.mint("ux_behavior.dispatch", {"ux_action": "vault.wipe"})
    wrong = Channel.boot(
        FastAPI(),
        config=ChannelConfig.development(secret="x" * 40, allow_memory_stores=True),
    ).mint("ux_behavior.dispatch", {"ux_action": "vault.wipe"})

    served = _Served(asgi)
    try:
        with httpx.Client(base_url=served.base) as client:
            assert _post(client, None).status_code == 401
            assert behavior.get("vault").wiped is False
            assert _post(client, wrong).status_code == 401
            assert behavior.get("vault").wiped is False
            forged_response = _post(client, forged)
            assert forged_response.status_code == 401
            assert behavior.get("vault").wiped is False
    finally:
        served.stop()


def test_explicit_secret_rejects_forged_public_constant(
    monkeypatch: pytest.MonkeyPatch,
):
    """A real secret already rejects the constant. Keep that after the dev path changes."""
    _clear(monkeypatch)
    monkeypatch.delenv("DEBUG", raising=False)
    real = "s" * 40

    asgi = FastAPI()
    behavior = Behavior.boot(title="Victim")
    behavior.add(Vault)
    behavior.region(lambda: "<div id='app.root'>ok</div>", uid="app.root")
    wire = behavior.attach(asgi, secret=real)
    assert wire.config.secret == real

    forged = Channel.boot(
        FastAPI(),
        config=ChannelConfig.development(
            secret=PUBLIC_DEV_SECRET, allow_memory_stores=True
        ),
    ).mint("ux_behavior.dispatch", {"ux_action": "vault.wipe"})

    served = _Served(asgi)
    try:
        with httpx.Client(base_url=served.base) as client:
            response = _post(client, forged)
            assert response.status_code == 401
            assert behavior.get("vault").wiped is False
    finally:
        served.stop()
