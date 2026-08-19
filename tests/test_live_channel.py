"""Live integration tests — require ux-channel (+ FastAPI for attach).

Run::

    pip install -e ".[dev]"
    pip install -e "git+https://github.com/bitplorer/ux-channel.git#subdirectory=python#egg=ux-channel"
    pip install fastapi httpx
    pytest tests/test_live_channel.py -q

Without Channel these tests are skipped (importorskip).
"""

from __future__ import annotations

import pytest

pytest.importorskip("ux_channel")
pytest.importorskip("fastapi")

from fastapi import FastAPI

from ux_behavior import Behavior, Component, action, notify, open, update
from ux_behavior.ops import Op
from ux_behavior.wire import Result, attach, attach_info, present, probe
from ux_behavior.wire.compose import Conflict


class Counter(Component):
    id = "counter"

    def __init__(self) -> None:
        self.n = 0

    def render(self) -> str:
        return f"<span id='counter'>{self.n}</span>"

    @action(caps=())
    def inc(self, by: int = 1):
        self.n += by
        return None

    @action(caps=())
    def set_ops(self, by: int = 1):
        self.n = by
        return [update("counter", self.render()), notify(f"set {by}")]

    @action(caps=())
    def leak(self):
        return [Op("secret", "leak", {})]


def test_live_probe_present():
    assert present() is True
    p = probe()
    assert p["ux_channel"] is True


def test_live_dispatch_dirty_and_explicit():
    app = Behavior.boot(title="Live")
    app.add(Counter)
    ops = app.dispatch("counter.inc", by=3)
    assert app.get("counter").n == 3
    assert ops[0].pair == ("ui.dom", "morph")
    assert "3" in str(ops[0].payload["patch"])

    ops2 = app.dispatch("counter.set_ops", by=9)
    assert app.get("counter").n == 9
    assert len(ops2) == 2
    assert ops2[0].pair == ("ui.dom", "morph")
    assert ops2[1].pair == ("log", "append")


def test_live_stamp_rejects_unstamped():
    app = Behavior.boot()
    app.add(Counter)
    with pytest.raises(PermissionError, match="stamp"):
        app.dispatch("counter.leak")


def test_live_attach_asgi():
    app = Behavior.boot(title="LiveAttach")
    app.add(Counter)
    app.region(lambda: "<div id='app.root'>ok</div>", uid="app.root")
    asgi = FastAPI()
    wire = app.attach(asgi)
    assert wire is not None
    assert type(wire).__name__ == "Channel"
    info = attach_info(app)
    assert info["attached"] is True
    assert info["ready_for_live"] is True
    assert app.attach(asgi) is wire  # idempotent


def test_live_attach_none_soft():
    app = Behavior.boot()
    assert attach(app, None) is None


def test_live_chrome_open_close():
    app = Behavior.boot()

    class C(Component):
        id = "c"

        def render(self):
            return ""

        @action(caps=())
        def open_sheet(self):
            return list(open("sheet", key="cart"))

        @action(caps=())
        def close_all(self):
            from ux_behavior import close

            return list(close())

    app.add(C)
    ops = app.dispatch("c.open_sheet")
    assert any(
        o.pair == ("kv", "set") and o.payload.get("key") == "ui.overlay.open"
        for o in ops
    )
    ops2 = app.dispatch("c.close_all")
    assert any(
        o.pair == ("kv", "set") and o.payload.get("value") is False for o in ops2
    )


def test_live_result_xor():
    with pytest.raises(Conflict):
        (
            Result()
            .morph("#x", "<a/>")
            .motion(
                {
                    "op": "transition.play",
                    "plan": {"target": "#x", "html": "<b/>"},
                }
            )
            .build()
        )


def test_live_result_happy():
    ops = Result().morph("#x", "<a/>").navigate("/y").build()
    assert any(isinstance(o, dict) and o.get("op") == "morph" for o in ops)
    assert any(isinstance(o, dict) and o.get("op") == "navigate" for o in ops)
    # navigate ordered last
    assert ops[-1].get("op") == "navigate"


def test_live_channel_dispatch_handler_registered():
    app = Behavior.boot(title="Dispatch")
    app.add(Counter)
    app.region(lambda: app.get("counter").render())
    asgi = FastAPI()
    wire = app.attach(asgi)
    assert wire is not None
    assert getattr(app, "_dispatch", None) is not None
    ops = app.dispatch("counter.inc", by=1)
    assert app.get("counter").n == 1
    assert ops


def test_live_doctor_still_clean():
    from ux_behavior.isolation import doctor

    assert doctor() == []
