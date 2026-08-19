"""Online (HTTP) matrix — parity with offline test_examples_matrix / test_every_mode.

Runs the same public / protected / trust / emit / validation cases over a real
HTTP server so offline and online coverage stay equally broad.

Channel attach remains optional (test_live_channel.py); this file always runs.
"""

from __future__ import annotations

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
    RefState,
    action,
    follow_up,
    go,
    notify,
    open,
    update,
)


# ── shared graph (mirrors offline examples matrix) ──


class Tabs(Component):
    id = "tabs"
    tab = MorphState("a")

    def render(self):
        return f"<div id='tabs'>{self.tab}</div>"

    @action(caps=())
    def select(self, tab: str = "a"):
        self.tab = tab
        return None

    @action(caps=())
    async def select_async(self, tab: str = "a"):
        self.tab = tab
        return None


class Toasts(Component):
    id = "toasts"
    items = MorphState(())
    _seq = RefState(0)

    def render(self):
        return f"<div id='toasts'></div>"

    @action(caps=())
    def push(self, message: str = ""):
        self._seq = int(self._seq or 0) + 1
        row = dict(id=str(self._seq), message=message)
        self.items = tuple(self.items or ()) + (row,)
        return None


class Modal(Component):
    id = "modal"
    open_flag = MorphState(False)

    def render(self):
        return f"<div id='modal'></div>"

    @action(caps=())
    def show(self):
        self.open_flag = True
        return [open("modal")]


class Carousel(Component):
    id = "carousel"
    index = MorphState(0)

    def render(self):
        return f"<div id='carousel'>{self.index}</div>"

    @action(caps=())
    def next(self):
        self.index = (int(self.index) + 1) % 3
        return None


class Confirm(Component):
    id = "confirm"
    open_flag = MorphState(False)
    target = RefState("")

    def render(self):
        return f"<div id='confirm'></div>"

    @action(caps=())
    def ask(self, id: str = ""):
        self.target, self.open_flag = id, True
        return None

    @action(caps=("items.delete",))
    def confirm(self):
        self.open_flag, self.target = False, ""
        return [notify("deleted")]


class Grid(Component):
    id = "grid"
    items = MorphState(())
    loading = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<div id='grid'></div>"

    @action(caps=())
    def more(self):
        self.loading = True
        self._req = int(self._req or 0) + 1
        return None

    @action(caps=())
    def apply_page(self, items=None, token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.loading = False
        self.items = tuple(self.items or ()) + tuple(items or ())
        return None


class Like(Component):
    id = "like"
    liked = MorphState(False)
    count = MorphState(0)

    def render(self):
        return f"<div id='like'></div>"

    @action(caps=())
    def toggle(self):
        self.liked = not bool(self.liked)
        self.count = int(self.count) + (1 if self.liked else -1)
        return None


class Table(Component):
    id = "table"
    selected = MorphState(())

    def render(self):
        return f"<div id='table'></div>"

    @action(caps=())
    def toggle(self, id: str = ""):
        s = set(self.selected or ())
        s.symmetric_difference_update({id})
        self.selected = tuple(sorted(s))
        return None

    @action(caps=("items.bulk_delete",))
    def bulk_delete(self):
        self.selected = ()
        return [notify("bulk")]


class Checkout(Component):
    id = "checkout"
    status = MorphState("idle")

    def render(self):
        return f"<div id='checkout'></div>"

    @action(caps=())
    def start(self):
        follow_up("paid", "checkout.finish")
        self.status = "awaiting"
        return [notify("pay")]

    @action(caps=("checkout.complete",))
    def finish(self):
        self.status = "paid"
        return [go("/thanks")]


class Form(Component):
    id = "form"
    name = MorphState("")

    def render(self):
        return f"<form id='form'></form>"

    @action(caps=())
    def save(self, name: str = ""):
        if not str(name).strip():
            return [update("form.name-error", "Required")]
        self.name = name.strip()
        return [notify("Saved")]


class Versions(Component):
    id = "versions"
    selected = MorphState("")

    def render(self):
        return f"<div id='versions'></div>"

    @action(caps=())
    def select(self, id: str = ""):
        self.selected = id
        return None

    @action(caps=("docs.restore",))
    def restore(self):
        return [notify(f"restored {self.selected}")]


class Tree(Component):
    id = "tree"
    expanded = MorphState(())

    def render(self):
        return f"<div id='tree'></div>"

    @action(caps=())
    def toggle(self, id: str = ""):
        s = set(self.expanded or ())
        if id in s:
            s.remove(id)
        else:
            s.add(id)
        self.expanded = tuple(sorted(s))
        return None


class Accordion(Component):
    id = "accordion"
    open_id = MorphState("")

    def render(self):
        return f"<div id='accordion'></div>"

    @action(caps=())
    def toggle(self, id: str = ""):
        self.open_id = "" if self.open_id == id else id
        return None


class Drawer(Component):
    id = "drawer"
    open_flag = MorphState(False)

    def render(self):
        return f"<div id='drawer'></div>"

    @action(caps=())
    def show(self):
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


def _build():
    app = Behavior.boot("online-matrix", strict_caps=True)
    for C in (
        Tabs,
        Toasts,
        Modal,
        Carousel,
        Confirm,
        Grid,
        Like,
        Table,
        Checkout,
        Form,
        Versions,
        Tree,
        Accordion,
        Drawer,
        Filters,
        Typeahead,
        Menu,
    ):
        app.add(C)
    return app


class _Server:
    """Tiny HTTP edge: /dispatch, /emit, /health — same semantics as production Host."""

    def __init__(self, app: Behavior, host: str = "127.0.0.1", port: int = 0):
        self.app = app

        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, code, obj):
                body = json.dumps(obj, default=str).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.startswith("/health"):
                    return self._json(
                        200,
                        {"ok": True, "actions": outer.app.actions()},
                    )
                self._json(404, {"error": "not found"})

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                data = json.loads(self.rfile.read(n) or b"{}")
                path = self.path.split("?")[0]
                try:
                    if path == "/dispatch":
                        args = dict(data.get("args") or {})
                        if data.get("trusted"):
                            args["_trusted"] = True
                        ops = outer.app.dispatch(data["action"], **args)
                        return self._json(
                            200,
                            {
                                "ok": True,
                                "ops": [
                                    {"fq": o.fq, "payload": o.payload}
                                    for o in (ops or [])
                                ],
                            },
                        )
                    if path == "/emit":
                        ops = outer.app.emit(str(data.get("event") or ""))
                        return self._json(
                            200,
                            {
                                "ok": True,
                                "ops": [
                                    {"fq": o.fq, "payload": o.payload}
                                    for o in (ops or [])
                                ],
                            },
                        )
                    return self._json(404, {"error": "not found"})
                except AuthorityError as e:
                    return self._json(403, {"ok": False, "error": str(e)})
                except TypeError as e:
                    return self._json(400, {"ok": False, "error": f"TypeError: {e}"})
                except Exception as e:
                    return self._json(
                        400, {"ok": False, "error": f"{type(e).__name__}: {e}"}
                    )

        self._httpd = HTTPServer((host, port), H)
        self.port = self._httpd.server_address[1]
        self.base = f"http://{host}:{self.port}"
        self._t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._t.start()
        time.sleep(0.05)

    def close(self):
        self._httpd.shutdown()

    def post(self, path: str, obj: dict):
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

    def get(self, path: str):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, json.load(r)


@pytest.fixture(scope="module")
def online():
    app = _build()
    srv = _Server(app)
    yield app, srv
    srv.close()


# ── cases (same breadth as offline PUBLIC_SYNC + extras) ──

PUBLIC = [
    ("tabs.select", {"tab": "shop"}),
    ("toasts.push", {"message": "hi"}),
    ("modal.show", {}),
    ("carousel.next", {}),
    ("confirm.ask", {"id": "x"}),
    ("grid.more", {}),
    ("like.toggle", {}),
    ("table.toggle", {"id": "r1"}),
    ("form.save", {"name": "Ada"}),
    ("tree.toggle", {"id": "n1"}),
    ("versions.select", {"id": "v1"}),
    ("accordion.toggle", {"id": "s1"}),
    ("drawer.show", {}),
    ("filters.apply", {"q": "tee"}),
    ("typeahead.type", {"q": "alp"}),
    ("menu.toggle", {}),
    ("menu.choose", {"v": "profile"}),
]

PROTECTED = [
    "confirm.confirm",
    "table.bulk_delete",
    "checkout.finish",
    "versions.restore",
]


def test_online_health(online):
    app, srv = online
    code, body = srv.get("/health")
    assert code == 200 and body["ok"]
    assert len(body["actions"]) >= 20


@pytest.mark.parametrize("action,kwargs", PUBLIC)
def test_online_public(online, action, kwargs):
    _, srv = online
    code, body = srv.post("/dispatch", {"action": action, "args": kwargs})
    assert code == 200 and body["ok"], body


@pytest.mark.parametrize("action", PROTECTED)
def test_online_protected_refuses(online, action):
    _, srv = online
    code, body = srv.post("/dispatch", {"action": action, "args": {}})
    assert code == 403 and not body["ok"]
    assert "Cap" in body["error"] or "cap" in body["error"].lower()


@pytest.mark.parametrize("action", PROTECTED)
def test_online_protected_trusted(online, action):
    _, srv = online
    code, body = srv.post(
        "/dispatch", {"action": action, "args": {}, "trusted": True}
    )
    assert code == 200 and body["ok"], body


def test_online_sync_rejects_async_action(online):
    _, srv = online
    code, body = srv.post(
        "/dispatch", {"action": "tabs.select_async", "args": {"tab": "x"}}
    )
    assert code == 400
    assert "async" in body["error"].lower()


def test_online_form_validation(online):
    _, srv = online
    code, body = srv.post("/dispatch", {"action": "form.save", "args": {"name": ""}})
    assert code == 200 and body["ok"]
    assert body["ops"] and "error" in body["ops"][0]["payload"].get("target", "")


def test_online_checkout_emit(online):
    app, srv = online
    code, body = srv.post("/dispatch", {"action": "checkout.start", "args": {}})
    assert code == 200 and body["ok"]
    code, body = srv.post("/emit", {"event": "paid"})
    assert code == 200 and body["ok"]
    assert app.get("checkout").status == "paid"


def test_online_state_after_public(online):
    app, srv = online
    srv.post("/dispatch", {"action": "tabs.select", "args": {"tab": "live"}})
    srv.post("/dispatch", {"action": "filters.apply", "args": {"q": "boot"}})
    srv.post("/dispatch", {"action": "drawer.show", "args": {}})
    assert app.get("tabs").tab == "live"
    assert app.get("filters").q == "boot"
    assert app.get("drawer").open_flag is True


def test_online_submit_parity_via_dispatch(online):
    """submit is offline-only helper; online Hosts use dispatch — assert same action."""
    app, srv = online
    code, body = srv.post("/dispatch", {"action": "like.toggle", "args": {}})
    assert code == 200
    # second toggle flips back if already liked from PUBLIC run order — just ensure no error
    assert body["ok"]
