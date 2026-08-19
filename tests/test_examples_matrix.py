"""Mode matrix applied to every major example family: sync/async × public/protected/trust.

One Behavior graph holds representative units from widgets, complex, nested, residual.
"""

from __future__ import annotations

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
    close,
    update,
)


# ─── Representative components (examples distilled) ───


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
        self.items = tuple(self.items or ()) + ({{"id": str(self._seq), "message": message}},)
        return None

    @action(caps=())
    async def push_async(self, message: str = ""):
        return self.push(message=message)


class Modal(Component):
    id = "modal"
    open_flag = MorphState(False)

    def render(self):
        return f"<div id='modal'></div>"

    @action(caps=())
    def show(self):
        self.open_flag = True
        return [open("modal")]

    @action(caps=())
    async def show_async(self):
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

    @action(caps=())
    async def next_async(self):
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

    @action(caps=("items.delete",))
    async def confirm_async(self):
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

    @action(caps=())
    async def more_async(self):
        return self.more()


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

    @action(caps=())
    async def toggle_async(self):
        return self.toggle()


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

    @action(caps=("items.bulk_delete",))
    async def bulk_delete_async(self):
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

    @action(caps=("checkout.complete",))
    async def finish_async(self):
        self.status = "paid"
        return [go("/thanks")]

    @action(caps=())
    def start_async_finish(self):
        follow_up("apaid", "checkout.finish_async")
        self.status = "awaiting"
        return [notify("pay")]


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

    @action(caps=())
    async def save_async(self, name: str = ""):
        return self.save(name=name)


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

    @action(caps=("docs.restore",))
    async def restore_async(self):
        return [notify(f"restored {self.selected}")]


class Tree(Component):
    id = "tree"
    expanded = MorphState(())
    selected = MorphState("")

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

    @action(caps=())
    async def toggle_async(self, id: str = ""):
        return self.toggle(id=id)


def build():
    app = Behavior.boot(strict_caps=True)
    for C in (
        Tabs, Toasts, Modal, Carousel, Confirm, Grid, Like, Table,
        Checkout, Form, Versions, Tree,
    ):
        app.add(C)
    return app


# ─── Public examples: sync + async entry ───

PUBLIC_SYNC = [
    ("tabs.select", {"tab": "b"}),
    ("toasts.push", {"message": "x"}),
    ("modal.show", {}),
    ("carousel.next", {}),
    ("confirm.ask", {"id": "1"}),
    ("grid.more", {}),
    ("like.toggle", {}),
    ("table.toggle", {"id": "r1"}),
    ("form.save", {"name": "Ada"}),
    ("tree.toggle", {"id": "n1"}),
    ("versions.select", {"id": "v1"}),
]

PUBLIC_ASYNC_ACTIONS = [
    ("tabs.select_async", {"tab": "c"}),
    ("toasts.push_async", {"message": "y"}),
    ("modal.show_async", {}),
    ("carousel.next_async", {}),
    ("grid.more_async", {}),
    ("like.toggle_async", {}),
    ("form.save_async", {"name": "Bob"}),
    ("tree.toggle_async", {"id": "n2"}),
]


@pytest.mark.parametrize("action,kwargs", PUBLIC_SYNC)
def test_public_sync_dispatch(action, kwargs):
    app = build()
    ops = app.dispatch(action, **kwargs)
    assert ops is not None


@pytest.mark.parametrize("action,kwargs", PUBLIC_SYNC)
@pytest.mark.asyncio
async def test_public_async_entry_sync_action(action, kwargs):
    app = build()
    ops = await app.async_dispatch(action, **kwargs)
    assert ops is not None


@pytest.mark.parametrize("action,kwargs", PUBLIC_ASYNC_ACTIONS)
def test_public_async_action_rejected_on_sync_entry(action, kwargs):
    app = build()
    with pytest.raises(TypeError, match="async"):
        app.dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", PUBLIC_ASYNC_ACTIONS)
@pytest.mark.asyncio
async def test_public_async_action_on_async_entry(action, kwargs):
    app = build()
    ops = await app.async_dispatch(action, **kwargs)
    assert ops is not None


# ─── Protected examples: refuse / trust / trusted / async ───

PROTECTED_SYNC = [
    ("confirm.confirm", {}),
    ("table.bulk_delete", {}),
    ("checkout.finish", {}),
    ("versions.restore", {}),
]

PROTECTED_ASYNC = [
    ("confirm.confirm_async", {}),
    ("table.bulk_delete_async", {}),
    ("checkout.finish_async", {}),
    ("versions.restore_async", {}),
]


@pytest.mark.parametrize("action,kwargs", PROTECTED_SYNC)
def test_protected_sync_refuses_offline(action, kwargs):
    app = build()
    with pytest.raises(AuthorityError):
        app.dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", PROTECTED_SYNC)
def test_protected_sync_trust(action, kwargs):
    app = build()
    with app.trust():
        ops = app.dispatch(action, **kwargs)
    assert ops is not None


@pytest.mark.parametrize("action,kwargs", PROTECTED_SYNC)
def test_protected_sync_trusted_kwarg(action, kwargs):
    app = build()
    ops = app.dispatch(action, _trusted=True, **kwargs)
    assert ops is not None


@pytest.mark.parametrize("action,kwargs", PROTECTED_SYNC)
@pytest.mark.asyncio
async def test_protected_async_entry_sync_action_refuses(action, kwargs):
    app = build()
    with pytest.raises(AuthorityError):
        await app.async_dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", PROTECTED_SYNC)
@pytest.mark.asyncio
async def test_protected_async_entry_sync_action_trusted(action, kwargs):
    app = build()
    ops = await app.async_dispatch(action, _trusted=True, **kwargs)
    assert ops is not None


@pytest.mark.parametrize("action,kwargs", PROTECTED_ASYNC)
def test_protected_async_action_rejected_on_sync_entry(action, kwargs):
    app = build()
    with pytest.raises(TypeError, match="async"):
        app.dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", PROTECTED_ASYNC)
@pytest.mark.asyncio
async def test_protected_async_action_refuses_offline(action, kwargs):
    app = build()
    with pytest.raises(AuthorityError):
        await app.async_dispatch(action, **kwargs)


@pytest.mark.parametrize("action,kwargs", PROTECTED_ASYNC)
@pytest.mark.asyncio
async def test_protected_async_action_trusted(action, kwargs):
    app = build()
    ops = await app.async_dispatch(action, _trusted=True, **kwargs)
    assert ops is not None


# ─── Continuations (emit sync + async) ───

def test_checkout_emit_sync():
    app = build()
    app.dispatch("checkout.start")
    app.emit("paid")
    assert app.get("checkout").status == "paid"


@pytest.mark.asyncio
async def test_checkout_async_emit_sync_finish():
    app = build()
    app.dispatch("checkout.start")
    await app.async_emit("paid")
    assert app.get("checkout").status == "paid"


@pytest.mark.asyncio
async def test_checkout_async_emit_async_finish():
    app = build()
    app.dispatch("checkout.start_async_finish")
    await app.async_emit("apaid")
    assert app.get("checkout").status == "paid"


# ─── Validation both entries ───

def test_form_validation_sync():
    app = build()
    ops = app.dispatch("form.save", name="")
    assert "error" in ops[0].payload["target"]


@pytest.mark.asyncio
async def test_form_validation_async():
    app = build()
    ops = await app.async_dispatch("form.save", name="")
    assert "error" in ops[0].payload["target"]


# ─── control offline for a sample of public actions ───

def test_control_offline_samples():
    app = build()
    for meth in (
        app.get("tabs").select,
        app.get("carousel").next,
        app.get("like").toggle,
    ):
        attrs = app.control(meth)
        assert "data_action" in attrs
        assert attrs.get("data_cap", "") == ""
