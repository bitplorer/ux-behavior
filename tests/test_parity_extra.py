"""Close offline/online coverage gaps.

Offline: accordion, drawer, filters, typeahead, menu (+ async).
Online: POST /async_dispatch, /async_emit, protected trusted paths.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    MorphState,
    action,
    follow_up,
    go,
    notify,
)


class Accordion(Component):
    id = "accordion"
    open_id = MorphState("")

    def render(self):
        return f"<div id='accordion'></div>"

    @action(caps=())
    def toggle(self, id: str = ""):
        self.open_id = "" if self.open_id == id else id
        return None

    @action(caps=())
    async def toggle_async(self, id: str = ""):
        return self.toggle(id=id)


class Drawer(Component):
    id = "drawer"
    open_flag = MorphState(False)

    def render(self):
        return f"<div id='drawer'></div>"

    @action(caps=())
    def show(self):
        self.open_flag = True
        return None

    @action(caps=())
    async def show_async(self):
        self.open_flag = True
        return None


class Filters(Component):
    id = "filters"
    q = MorphState("")

    def render(self):
        return f"<div id='filters'></div>"

    @action(caps=())
    def apply(self, q: str = ""):
        self.q = q
        return None

    @action(caps=())
    async def apply_async(self, q: str = ""):
        self.q = q
        return None


class Typeahead(Component):
    id = "typeahead"
    query = MorphState("")
    hits = MorphState(())

    def render(self):
        return f"<div id='typeahead'></div>"

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        self.hits = tuple(x for x in ("alpha", "alpine", "beta") if q.lower() in x)
        return None

    @action(caps=())
    async def type_async(self, q: str = ""):
        return self.type(q=q)


class Menu(Component):
    id = "menu"
    open_flag = MorphState(False)
    value = MorphState("")

    def render(self):
        return f"<div id='menu'></div>"

    @action(caps=())
    def toggle(self):
        self.open_flag = not bool(self.open_flag)
        return None

    @action(caps=())
    def choose(self, v: str = ""):
        self.value, self.open_flag = v, False
        return None


class Sec(Component):
    id = "sec"
    n = MorphState(0)

    def render(self):
        return f"<div id='sec'></div>"

    @action(caps=("sec.write",))
    def write(self, n: int = 0):
        self.n = n
        return [notify("wrote")]

    @action(caps=("sec.write",))
    async def write_async(self, n: int = 0):
        self.n = n
        return [notify("wrote")]

    @action(caps=())
    def start(self):
        follow_up("sec.done", "sec.write", n=9)
        return [notify("armed")]


def _offline_app():
    app = Behavior.boot(strict_caps=True)
    for C in (Accordion, Drawer, Filters, Typeahead, Menu, Sec):
        app.add(C)
    return app


OFF_PUBLIC = [
    ("accordion.toggle", {"id": "s1"}),
    ("drawer.show", {}),
    ("filters.apply", {"q": "tee"}),
    ("typeahead.type", {"q": "alp"}),
    ("menu.toggle", {}),
    ("menu.choose", {"v": "profile"}),
]

OFF_PUBLIC_ASYNC = [
    ("accordion.toggle_async", {"id": "s2"}),
    ("drawer.show_async", {}),
    ("filters.apply_async", {"q": "hat"}),
    ("typeahead.type_async", {"q": "be"}),
]


@pytest.mark.parametrize("action,kwargs", OFF_PUBLIC)
def test_offline_extra_public_sync(action, kwargs):
    app = _offline_app()
    assert app.dispatch(action, **kwargs) is not None


@pytest.mark.parametrize("action,kwargs", OFF_PUBLIC)
@pytest.mark.asyncio
async def test_offline_extra_public_async_entry(action, kwargs):
    app = _offline_app()
    assert await app.async_dispatch(action, **kwargs) is not None


@pytest.mark.parametrize("action,kwargs", OFF_PUBLIC_ASYNC)
def test_offline_extra_async_rejected_sync(action, kwargs):
    app = _offline_app()
    with pytest.raises(TypeError, match="async"):
        app.dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", OFF_PUBLIC_ASYNC)
@pytest.mark.asyncio
async def test_offline_extra_async_ok(action, kwargs):
    app = _offline_app()
    assert await app.async_dispatch(action, **kwargs) is not None


def test_offline_extra_protected_refuse_trust():
    app = _offline_app()
    with pytest.raises(AuthorityError):
        app.dispatch("sec.write", n=1)
    with app.trust():
        app.dispatch("sec.write", n=2)
    assert app.get("sec").n == 2
    app.dispatch("sec.write", n=3, _trusted=True)
    assert app.get("sec").n == 3


@pytest.mark.asyncio
async def test_offline_extra_protected_async():
    app = _offline_app()
    with pytest.raises(AuthorityError):
        await app.async_dispatch("sec.write_async", n=1)
    await app.async_dispatch("sec.write_async", n=4, _trusted=True)
    assert app.get("sec").n == 4


def test_offline_extra_emit():
    app = _offline_app()
    app.dispatch("sec.start")
    app.emit("sec.done")
    assert app.get("sec").n == 9


class Pub(Component):
    id = "pub"
    n = MorphState(0)

    def render(self):
        return f"<div id='pub'></div>"

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
        return None

    @action(caps=())
    async def inc_async(self):
        self.n = int(self.n) + 10
        return None


class Pay(Component):
    id = "pay"
    status = MorphState("idle")

    def render(self):
        return f"<div id='pay'></div>"

    @action(caps=())
    def start(self):
        follow_up("paid", "pay.finish")
        self.status = "awaiting"
        return [notify("go")]

    @action(caps=("pay.done",))
    def finish(self):
        self.status = "paid"
        return [go("/ok")]


def _online_app():
    app = Behavior.boot(strict_caps=True)
    app.add(Pub)
    app.add(Pay)
    app.add(Sec)
    return app


class HttpEdge:
    def __init__(self, app):
        self.app = app
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, code, obj):
                b = json.dumps(obj, default=str).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                data = json.loads(self.rfile.read(n) or b"{}")
                path = self.path.split("?")[0]
                try:
                    args = dict(data.get("args") or {})
                    if data.get("trusted"):
                        args["_trusted"] = True
                    if path == "/dispatch":
                        ops = outer.app.dispatch(data["action"], **args)
                    elif path == "/async_dispatch":
                        ops = asyncio.run(
                            outer.app.async_dispatch(data["action"], **args)
                        )
                    elif path == "/emit":
                        ops = outer.app.emit(str(data.get("event") or ""))
                    elif path == "/async_emit":
                        ops = asyncio.run(
                            outer.app.async_emit(str(data.get("event") or ""))
                        )
                    else:
                        return self._json(404, {"ok": False})
                    return self._json(
                        200,
                        {"ok": True, "ops": [{"fq": o.fq} for o in (ops or [])]},
                    )
                except AuthorityError as e:
                    return self._json(403, {"ok": False, "error": str(e)})
                except TypeError as e:
                    return self._json(400, {"ok": False, "error": f"TypeError: {e}"})
                except Exception as e:
                    return self._json(
                        400, {"ok": False, "error": f"{type(e).__name__}: {e}"}
                    )

        self._httpd = HTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        time.sleep(0.05)

    def close(self):
        self._httpd.shutdown()

    def post(self, path, obj):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(obj).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)


@pytest.fixture
def edge():
    app = _online_app()
    e = HttpEdge(app)
    yield app, e
    e.close()


def test_online_async_dispatch_public(edge):
    _, e = edge
    code, body = e.post("/async_dispatch", {"action": "pub.inc", "args": {}})
    assert code == 200 and body["ok"]


def test_online_async_dispatch_async_action(edge):
    app, e = edge
    code, body = e.post("/async_dispatch", {"action": "pub.inc_async", "args": {}})
    assert code == 200 and body["ok"]
    assert app.get("pub").n == 10


def test_online_dispatch_rejects_async_action(edge):
    _, e = edge
    code, body = e.post("/dispatch", {"action": "pub.inc_async", "args": {}})
    assert code == 400 and "async" in body["error"].lower()


def test_online_async_dispatch_protected_refuse(edge):
    _, e = edge
    code, body = e.post("/async_dispatch", {"action": "sec.write", "args": {"n": 1}})
    assert code == 403


def test_online_async_dispatch_protected_trusted(edge):
    app, e = edge
    code, body = e.post(
        "/async_dispatch",
        {"action": "sec.write", "args": {"n": 5}, "trusted": True},
    )
    assert code == 200 and body["ok"]
    assert app.get("sec").n == 5


def test_online_async_emit(edge):
    app, e = edge
    e.post("/dispatch", {"action": "pay.start", "args": {}})
    code, body = e.post("/async_emit", {"event": "paid"})
    assert code == 200 and body["ok"]
    assert app.get("pay").status == "paid"
