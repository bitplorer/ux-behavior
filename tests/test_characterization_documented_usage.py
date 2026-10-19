"""Characterization of documented public usage.

Pins the stories in START_HERE, the README, tutorials 01–07, the Harbor
cart pilot, and the cookbook paths that match that contract.

Does not lock wire-secret fallbacks, browser-chosen trusted dispatch,
shared visitor planes, or other side effects that are not the documented
author path.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ux_behavior.root import _FRAMEWORK_TRUST
from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    ContinuationError,
    DictBackend,
    KeepState,
    MorphState,
    Op,
    PrefState,
    RefState,
    UiState,
    action,
    bind,
    close,
    confirm,
    follow_up,
    go,
    notify,
    open,
    select,
    submit_outcome,
    update,
)
from ux_behavior.isolation import doctor
from ux_behavior.local import LocalRuntime
from ux_behavior.wire import Conflict, Result


def test_cold_import_does_not_load_channel_or_cek():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    script = (
        "import sys\n"
        "import ux_behavior\n"
        "assert 'ux_behavior' in sys.modules\n"
        "assert 'ux_channel' not in sys.modules\n"
        "assert not any(name.startswith('cek_') for name in sys.modules)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_doctor_reports_no_violations():
    assert doctor() == []


def test_start_here_cart_badge_dispatch_and_registry():
    class CartBadge(Component):
        id = "cart.badge"
        count = MorphState(0)

        def render(self):
            return f"<button id='cart.badge'>{self.count}</button>"

        @action(caps=())
        def add(self, sku: str = ""):
            self.count = int(self.count) + 1
            return [notify("Added")]

    app = Behavior.boot(title="Cart")
    app.add(CartBadge)
    ops = app.dispatch("cart.badge.add", sku="tee")
    assert [op.pair for op in ops] == [("log", "append")]
    assert ops[0].payload["message"] == "Added"
    assert app.get("cart.badge").count == 1
    assert list(app.components().keys()) == ["cart.badge"]
    copied = app.components()
    copied.clear()
    assert list(app.components().keys()) == ["cart.badge"]


def test_readme_public_add_returns_notify_and_bumps_count():
    class Cart(Component):
        id = "cart"
        count = MorphState(0)

        def render(self):
            return f"<div id='cart'>{self.count}</div>"

        @action(caps=())
        def add(self, sku: str = ""):
            self.count = int(self.count) + 1
            return [notify("Added")]

    app = Behavior.boot("Shop", strict_caps=True)
    app.add(Cart)
    ops = app.dispatch("cart.add", sku="tee")
    assert ops[0].fq == "log.append"
    assert app.get("cart").count == 1
    assert app.actions("cart") == ["cart.add"]


def test_tutorial_01_return_none_morphs_dirty_counter():
    class Counter(Component):
        id = "counter"
        n = MorphState(0)

        def render(self):
            return f"<div id='counter'><span>{self.n}</span></div>"

        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            return None

    app = Behavior.boot(title="Demo")
    app.add(Counter)
    ops = app.dispatch("counter.inc")
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
    assert ops[0].payload["target"] == "counter"
    assert "1" in str(ops[0].payload["patch"])
    ops2 = app.dispatch("counter.inc")
    assert "2" in str(ops2[0].payload["patch"])
    assert app.get("counter").n == 2
    assert "counter.inc" in app.actions()


def test_tutorial_02_planes_ref_silence_and_host_store():
    class Workspace(Component):
        id = "ws"
        page = MorphState("home")
        menu_open = UiState(False)
        theme = PrefState("system", key="ui.theme")
        draft = KeepState("")
        render_ticks = RefState(0)

        def render(self):
            self.render_ticks = int(self.render_ticks or 0) + 1
            return (
                f"<section id='ws' data-page='{self.page}' data-theme='{self.theme}'>"
                f"<p>menu={'open' if self.menu_open else 'closed'}</p>"
                f"<pre>{self.draft}</pre>"
                f"</section>"
            )

        @action(caps=())
        def go(self, page: str = "home"):
            self.page = page
            self.menu_open = False
            return None

        @action(caps=())
        def set_theme(self, theme: str = "system"):
            self.theme = theme
            return None

        @action(caps=())
        def save_draft(self, text: str = ""):
            self.draft = text
            return None

        @action(caps=())
        def touch_ref_only(self):
            self.render_ticks = int(self.render_ticks or 0) + 1
            return None

    app = Behavior.boot()
    ws = app.add(Workspace)
    ops = app.dispatch("ws.go", page="settings")
    assert ops and ops[0].pair == ("ui.dom", "morph")
    assert ws.page == "settings"
    assert ws.menu_open is False

    app.dispatch("ws.set_theme", theme="dark")
    assert app.state.backend("client").data.get("ui.theme") == "dark"

    app.dispatch("ws.save_draft", text="hello")
    assert app.state.backend("store").data.get("ws.draft") == "hello"

    assert app.dispatch("ws.touch_ref_only") == []
    assert int(ws.render_ticks) >= 1

    kv = DictBackend()
    app.state.use("store", kv)
    app.dispatch("ws.save_draft", text="persisted")
    assert kv.data["ws.draft"] == "persisted"
    assert app.state.report["store"] == "host"
    assert app.state.is_locked("store") is True


def test_client_plane_refuses_money_shaped_write():
    class Cart(Component):
        id = "cart"
        price = MorphState(0, backend="client", key="cart.price")

        def render(self):
            return f"<div id='cart'>{self.price}</div>"

        @action(caps=())
        def set_price(self, price: int = 0):
            self.price = price
            return None

    app = Behavior.boot()
    app.add(Cart)
    with pytest.raises(AuthorityError, match="client plane"):
        app.dispatch("cart.set_price", price=10)


def test_tutorial_03_explicit_ops_chrome_and_stamp():
    class Panel(Component):
        id = "panel"
        page = MorphState("home")

        def render(self):
            return f"<div id='panel'>{self.page}</div>"

        @action(caps=())
        def explicit(self):
            return [update("ws", "<div id='ws'>hi</div>"), notify("saved")]

        @action(caps=())
        def navigate(self):
            return [go("/cart")]

        @action(caps=())
        def chrome(self):
            return list(open("modal.help"))

        @action(caps=())
        def after_submit(self):
            return submit_outcome("form.box", "<p>ok</p>", message="Done")

        @action(caps=())
        def unstamped(self):
            return [Op("orders", "place", {})]

        @action(caps=())
        def toast(self):
            return [Op("ui.notice", "push", {"message": "hi"})]

    app = Behavior.boot()
    app.add(Panel)

    ops = app.dispatch("panel.explicit")
    assert [op.pair for op in ops] == [("ui.dom", "morph"), ("log", "append")]
    assert ops[0].payload == {"target": "ws", "patch": "<div id='ws'>hi</div>"}

    nav = app.dispatch("panel.navigate")
    assert nav[0].pair == ("nav", "push")
    assert nav[0].payload["href"] == "/cart"

    chrome = app.dispatch("panel.chrome")
    _assert_stamped_chrome(chrome)

    outcome = app.dispatch("panel.after_submit")
    assert [op.pair for op in outcome] == [("ui.dom", "morph"), ("log", "append")]
    assert outcome[0].payload["target"] == "form.box"
    assert outcome[1].payload["message"] == "Done"

    with pytest.raises(PermissionError, match="session stamp"):
        app.dispatch("panel.unstamped")
    with pytest.raises(PermissionError):
        app.dispatch("panel.toast")

    app.use("effects")
    app.domain("orders", "1", [("orders", "place")])
    toasted = app.dispatch("panel.toast")
    assert toasted[0].fq == "ui.notice.push"
    placed = app.dispatch("panel.unstamped")
    assert placed[0].fq == "orders.place"


def test_chrome_close_select_and_confirm_are_stamped_ops():
    class Hud(Component):
        id = "hud"

        def render(self):
            return "<div id='hud'></div>"

        @action(caps=())
        def shut(self):
            return list(close())

        @action(caps=())
        def tab(self):
            return list(select("orders.tabs", "shipped"))

        @action(caps=())
        def ask(self):
            return list(confirm("Delete?", body="Cannot undo."))

    app = Behavior.boot()
    app.add(Hud)
    _assert_stamped_chrome(app.dispatch("hud.shut"))
    _assert_stamped_chrome(app.dispatch("hud.tab"))
    _assert_stamped_chrome(app.dispatch("hud.ask"))


def test_tutorial_04_typed_args_submit_and_exact_field_type():
    class Profile(Component):
        id = "profile"
        name = MorphState("")
        age = MorphState(0, type=int)

        def render(self):
            return f"<div id='profile'>{self.name}</div>"

        @action(caps=())
        def save(self, name: str = ""):
            self.name = name
            return None

        @action(caps=())
        def set_age(self, age: int = 0):
            self.age = age
            return None

    app = Behavior.boot()
    inst = app.add(Profile)
    saved = app.dispatch("profile.save", name="Ada")
    assert inst.name == "Ada"
    assert "Ada" in str(saved[0].payload["patch"])

    bad = app.dispatch("profile.save", name=123)
    assert bad[0].pair == ("ui.dom", "morph")
    assert bad[0].payload["target"] == "profile.save.name-error"
    assert inst.name == "Ada"

    via_submit = app.submit("profile.save", {"name": "Grace"})
    assert inst.name == "Grace"
    assert via_submit[0].pair == ("ui.dom", "morph")

    with pytest.raises(TypeError, match="no coerce"):
        inst.age = "1"


def test_tutorial_05_protected_action_needs_trust_door():
    class Orders(Component):
        id = "orders"
        menu_open = MorphState(False)

        def render(self):
            return f"<div id='orders'>{self.menu_open}</div>"

        @action(caps=())
        def open_menu(self):
            self.menu_open = True
            return None

        @action(caps=("orders.write",))
        def place(self, sku: str = ""):
            return [notify("placed")]

    app = Behavior.boot()
    app.add(Orders)
    app.dispatch("orders.open_menu")
    assert app.get("orders").menu_open is True

    with pytest.raises(AuthorityError) as caught:
        app.dispatch("orders.place", sku="x")
    assert caught.value.hint == ""
    assert any(event.code == "CAP_REQUIRED" for event in app.diagnostics.events)

    with app.trust():
        trusted = app.dispatch("orders.place", sku="x")
    assert trusted[0].payload["message"] == "placed"
    assert app.strict_caps is True

    again = app.dispatch("orders.place", sku="y", _trusted=_FRAMEWORK_TRUST)
    assert again[0].fq == "log.append"


def test_tutorial_06_follow_up_emit_with_fixed_args():
    class Orders(Component):
        id = "orders"
        status = MorphState("idle")

        def render(self):
            return f"<div id='orders'>{self.status}</div>"

        @action(caps=())
        def start_checkout(self, order_id: int = 0):
            follow_up("paid", "orders.confirm", order_id=order_id)
            self.status = "awaiting_payment"
            return [notify("Pay now")]

        @action(caps=())
        def confirm(self, order_id: int = 0):
            self.status = f"paid:{order_id}"
            return None

    app = Behavior.boot()
    app.add(Orders)
    app.dispatch("orders.start_checkout", order_id=1)
    assert "paid" in app.continuations
    assert app.continuations["paid"].action == "orders.confirm"
    assert app.get("orders").status == "awaiting_payment"

    ops = app.emit("paid")
    assert app.get("orders").status == "paid:1"
    assert ops and ops[0].pair == ("ui.dom", "morph")

    with pytest.raises(RuntimeError, match="during Behavior.dispatch"):
        follow_up("other", "orders.confirm")
    with pytest.raises(ContinuationError, match="no continuation"):
        app.emit("missing")


def test_tutorial_06_args_from_emit_maps_id_to_order_id():
    """Tutorial 06: emit(id=99) fills confirm(order_id=...) via args_from."""

    class Orders(Component):
        id = "orders"
        status = MorphState("idle")

        def render(self):
            return f"<div id='orders'>{self.status}</div>"

        @action(caps=())
        def start_checkout(self, order_id: int = 0):
            follow_up(
                "paid",
                "orders.confirm",
                args_from={"order_id": "id"},
            )
            self.status = "awaiting_payment"
            return [notify("Pay now")]

        @action(caps=())
        def confirm(self, order_id: int = 0):
            self.status = f"paid:{order_id}"
            return None

    app = Behavior.boot()
    app.add(Orders)
    app.dispatch("orders.start_checkout", order_id=1)
    app.emit("paid", id=99)
    assert app.get("orders").status == "paid:99"


def test_tutorial_07_async_action_uses_async_dispatch():
    class Saver(Component):
        id = "saver"
        ok = MorphState(False)

        def render(self):
            return f"<div id='saver'>{self.ok}</div>"

        @action(caps=())
        async def save(self):
            self.ok = True
            return None

    app = Behavior.boot()
    app.add(Saver)
    with pytest.raises(TypeError, match="async_dispatch"):
        app.dispatch("saver.save")

    import asyncio

    ops = asyncio.run(app.async_dispatch("saver.save"))
    assert app.get("saver").ok is True
    assert ops[0].pair == ("ui.dom", "morph")
    assert "True" in str(ops[0].payload["patch"])


def test_bind_and_ui_match_and_reject_unknown_kwargs():
    class Cart(Component):
        id = "cart"
        count = MorphState(0)

        def render(self):
            return f"<div id='cart'>{self.count}</div>"

        @action(caps=())
        def add(self, sku: str = ""):
            self.count = int(self.count) + 1
            return [notify(f"Added {sku}")]

    app = Behavior.boot("Shop")
    cart = app.add(Cart)
    attrs = bind(cart.add, sku="tee")
    assert attrs == cart.add.ui(sku="tee")
    assert attrs["data-ux-action"] == "cart.add"
    assert attrs["data-channel-action"] == "cart.add"
    assert "tee" in attrs["data-channel-args"]
    assert attrs["data-ux-arg-sku"] == "tee"
    with pytest.raises(TypeError, match="unexpected kwarg"):
        cart.add.ui(nope="x")


def test_control_offline_names_the_action_without_a_cap():
    class Cart(Component):
        id = "cart"

        def render(self):
            return "<div id='cart'></div>"

        @action(caps=())
        def add(self, sku: str = ""):
            return []

    app = Behavior.boot("Shop")
    app.add(Cart)
    attrs = app.control("cart.add", sku="tee")
    assert attrs["data_action"] == "cart.add"
    assert "tee" in attrs["data_args"]
    assert attrs["data_cap"] == ""
    assert any(event.code == "CONTROL_OFFLINE" for event in app.diagnostics.events)


def test_preview_blocks_session_and_store_writes():
    class Draft(Component):
        id = "draft"
        page = MorphState("home")
        note = KeepState("")

        def render(self):
            return f"<div id='draft'>{self.page}</div>"

        @action(caps=())
        def edit(self, page: str = "home"):
            self.page = page
            return None

        @action(caps=())
        def save_note(self, text: str = ""):
            self.note = text
            return None

    app = Behavior.boot()
    app.add(Draft)
    with app.preview():
        with pytest.raises(AuthorityError, match="preview cannot write"):
            app.dispatch("draft.edit", page="away")
        with pytest.raises(AuthorityError, match="preview cannot write store"):
            app.dispatch("draft.save_note", text="secret")
    assert app.get("draft").page == "home"
    assert app.get("draft").note == ""
    assert app.is_preview is False


def _assert_stamped_chrome(ops: list) -> None:
    """open/close/select/confirm dispatch as stamped kv and ui.dom.morph ops."""
    pairs = [op.pair for op in ops]
    assert pairs
    assert set(pairs) <= {("kv", "set"), ("kv", "delete"), ("ui.dom", "morph")}
    assert any(pair[0] == "kv" for pair in pairs)
    assert ("ui.dom", "morph") in pairs


def test_refresh_and_unknown_component():
    class Box(Component):
        id = "box"
        n = MorphState(3)

        def render(self):
            return f"<div id='box'>{self.n}</div>"

    app = Behavior.boot()
    app.add(Box)
    ops = app.refresh("box")
    assert len(ops) == 1
    assert ops[0].payload["target"] == "box"
    assert ">3<" in str(ops[0].payload["patch"])
    with pytest.raises(KeyError, match="unknown component id 'missing'"):
        app.get("missing")


def test_harbor_cart_pilot_matches_its_author_flow():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "harbor_cart_pilot", root / "examples" / "harbor_cart_pilot.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = Behavior.boot(title="Harbor pilot")
    app.add(module.Cart)
    runtime = LocalRuntime.bind(app)

    added = runtime.call("cart", "add", id="linen-01", qty=1)
    assert any(op.fq == "log.append" and "linen-01" in op.payload["message"] for op in added)
    assert app.get("cart").lines == [{"id": "linen-01", "qty": 1}]

    runtime.call("cart", "add", id="linen-01", qty=2)
    assert app.get("cart").lines == [{"id": "linen-01", "qty": 3}]

    promo = runtime.call("cart", "promo_apply", code="harbor10")
    assert app.get("cart").promo == "HARBOR10"
    assert any(op.payload.get("message") == "HARBOR10 applied" for op in promo)
    assert any(op.pair == ("ui.dom", "morph") and op.payload["target"] == "cart" for op in promo)

    unknown = runtime.call("cart", "promo_apply", code="nope")
    assert app.get("cart").promo == ""
    assert any(op.payload.get("message") == "Code not recognised" for op in unknown)

    shown = runtime.call("cart", "show")
    assert shown == [go("/cart")]

    runtime.call("cart", "remove", id="linen-01")
    assert app.get("cart").lines == []


def test_start_here_result_orders_navigate_last_and_rejects_xor():
    scene = type(
        "Scene",
        (),
        {
            "play": lambda self: {
                "ok": True,
                "ops": [
                    {
                        "op": "transition.play",
                        "plan": {
                            "kind": "plan",
                            "root": {
                                "kind": "track",
                                "target": "#view",
                                "html": "<section id='view'>x</section>",
                            },
                        },
                    }
                ],
            }
        },
    )()
    with pytest.raises(Conflict, match="XOR"):
        Result().morph("#view", "<section/>").motion(scene).build()

    quiet = type(
        "Scene",
        (),
        {
            "play": lambda self: {
                "ok": True,
                "ops": [
                    {
                        "op": "transition.play",
                        "plan": {
                            "kind": "plan",
                            "root": {"kind": "track", "target": "#view", "role": "enter"},
                        },
                    }
                ],
            }
        },
    )()
    ops = (
        Result()
        .navigate("/cart")
        .morph("#view", "<p>ok</p>")
        .motion(quiet)
        .build()
    )
    assert [op["op"] for op in ops] == ["morph", "transition.play", "navigate"]
    assert ops[-1]["href"] == "/cart"


def test_single_op_return_is_normalized_to_a_list():
    class Box(Component):
        id = "box"

        def render(self):
            return "<div id='box'></div>"

        @action(caps=())
        def ping(self):
            return notify("hi")

    app = Behavior.boot()
    app.add(Box)
    ops = app.dispatch("box.ping")
    assert ops == [notify("hi")]
