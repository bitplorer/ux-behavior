"""follow_up + emit + Cap posture."""

from __future__ import annotations

import contextvars
import gc

import pytest

from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    ContinuationError,
    MorphState,
    action,
    follow_up,
    notify,
)
from ux_behavior.events import _armed
from ux_behavior.root import _FRAMEWORK_TRUST


class Orders(Component):
    id = "orders"
    last = MorphState("")

    def render(self):
        return f"<div>{self.last}</div>"

    @action(caps=())
    def start(self):
        follow_up("paid", "orders.confirm", order_id=1)
        return [notify("awaiting payment")]

    @action(caps=())
    def confirm(self, order_id: int = 0):
        self.last = f"ok:{order_id}"
        return None

    @action(caps=("orders.write",))
    def secure(self):
        return [notify("secure")]


def test_follow_up_emit():
    app = Behavior.boot()
    app.add(Orders)
    ops = app.dispatch("orders.start")
    assert ops and ops[0].pair == ("log", "append")
    assert "paid" in app.continuations
    ops2 = app.emit("paid")
    assert app.get("orders").last == "ok:1"
    assert ops2  # dirty morph


def test_emit_unknown():
    app = Behavior.boot()
    app.add(Orders)
    with pytest.raises(ContinuationError):
        app.emit("missing")


def test_follow_up_outside_action():
    with pytest.raises(RuntimeError):
        follow_up("x", "orders.confirm")


def test_strict_caps_offline():
    app = Behavior.boot()
    app.add(Orders)
    with pytest.raises(AuthorityError):
        app.dispatch("orders.secure")
    ops = app.dispatch("orders.secure", _trusted=_FRAMEWORK_TRUST)
    assert ops


def test_strict_caps_off():
    app = Behavior.boot(strict_caps=False)
    app.add(Orders)
    assert app.dispatch("orders.secure")


def test_emit_keeps_unmapped_slots_when_args_from_is_empty():
    """emit(order_id=...) still binds when follow_up stored no args_from map."""

    class Desk(Component):
        id = "desk"
        last = MorphState("")

        def render(self):
            return f"<div>{self.last}</div>"

        @action(caps=())
        def arm(self):
            follow_up("paid", "desk.finish")
            return None

        @action(caps=())
        def finish(self, order_id: int = 0, note: str = ""):
            self.last = f"{order_id}:{note}"
            return None

    app = Behavior.boot()
    app.add(Desk)
    app.dispatch("desk.arm")
    app.emit("paid", order_id=7, note="rush")
    assert app.get("desk").last == "7:rush"


def test_args_from_drops_consumed_source_and_keeps_other_slots():
    """Mapped emit keys are not forwarded. Unmapped emit keys still bind."""

    class Desk(Component):
        id = "desk"
        last = MorphState("")

        def render(self):
            return f"<div>{self.last}</div>"

        @action(caps=())
        def arm(self):
            follow_up("paid", "desk.finish", args_from={"order_id": "id"})
            return None

        @action(caps=())
        def finish(self, order_id: int = 0, note: str = ""):
            self.last = f"{order_id}:{note}"
            return None

    app = Behavior.boot()
    app.add(Desk)
    app.dispatch("desk.arm")
    app.emit("paid", id=99, note="rush")
    assert app.get("desk").last == "99:rush"


def _armed_order(app: Behavior) -> str:
    return str(app.continuations["paid"].args["order"])


def test_armed_continuation_stays_in_the_context_that_armed_it():
    """Two contexts on one Behavior must not see each other's emit target."""

    class Desk(Component):
        id = "desk"

        def render(self):
            return "<div id='desk'></div>"

        @action(caps=())
        def arm(self, order: str = ""):
            follow_up("paid", "desk.finish", order=order)
            return None

        @action(caps=())
        def finish(self, order: str = ""):
            return None

    app = Behavior.boot()
    app.add(Desk)

    def arm(order: str) -> None:
        app.dispatch("desk.arm", order=order)

    ctx_a = contextvars.copy_context()
    ctx_b = contextvars.copy_context()
    ctx_a.run(arm, "alice")
    ctx_b.run(arm, "bob")

    assert ctx_a.run(_armed_order, app) == "alice"
    assert ctx_b.run(_armed_order, app) == "bob"
    assert "paid" not in app.continuations


def test_copied_context_does_not_replace_the_parent_continuation():
    """A write in a copied context must not change the parent's armed event."""

    class Desk(Component):
        id = "desk"

        def render(self):
            return "<div id='desk'></div>"

        @action(caps=())
        def arm(self, order: str = ""):
            follow_up("paid", "desk.finish", order=order)
            return None

        @action(caps=())
        def finish(self, order: str = ""):
            return None

    app = Behavior.boot()
    app.add(Desk)

    def arm_and_copy(order: str) -> contextvars.Context:
        app.dispatch("desk.arm", order=order)
        return contextvars.copy_context()

    parent = contextvars.copy_context()
    child = parent.run(arm_and_copy, "alice")
    child.run(app.dispatch, "desk.arm", order="bob")

    assert parent.run(_armed_order, app) == "alice"
    assert child.run(_armed_order, app) == "bob"


def _armed_scope_count() -> int:
    bag = _armed.get()
    if not bag:
        return 0
    return len(list(bag))


def test_twenty_collected_behaviors_leave_no_armed_scopes():
    """boot/follow_up/del/gc twenty times must not retain those scopes."""

    def run() -> int:
        _armed.set(None)
        for _ in range(20):
            app = Behavior.boot()
            app.add(Orders)
            app.dispatch("orders.start")
            del app
        gc.collect()
        return _armed_scope_count()

    assert contextvars.copy_context().run(run) == 0


def test_child_continuation_args_mutation_does_not_change_parent():
    """A copied context gets its own Continuation. Mutating args stays there."""

    class Desk(Component):
        id = "desk"

        def render(self):
            return "<div id='desk'></div>"

        @action(caps=())
        def arm(self, order: str = ""):
            follow_up("paid", "desk.finish", order=order)
            return None

        @action(caps=())
        def finish(self, order: str = ""):
            return None

    app = Behavior.boot()
    app.add(Desk)

    def arm_and_copy(order: str) -> contextvars.Context:
        app.dispatch("desk.arm", order=order)
        return contextvars.copy_context()

    def mutate() -> str:
        app.continuations["paid"].args["order"] = "hacked"
        return str(app.continuations["paid"].args["order"])

    parent = contextvars.copy_context()
    child = parent.run(arm_and_copy, "alice")
    assert child.run(mutate) == "hacked"
    assert parent.run(_armed_order, app) == "alice"


def test_child_list_append_in_args_leaves_parent_emit_unchanged():
    """Child appends to a list stored in args. Parent emit still sees the original."""

    class Desk(Component):
        id = "desk"
        seen = MorphState("")

        def render(self):
            return "<div id='desk'></div>"

        @action(caps=())
        def arm(self):
            follow_up("paid", "desk.finish", items=["a"])
            return None

        @action(caps=())
        def finish(self, items: list | None = None):
            self.seen = ",".join(str(part) for part in (items or []))
            return None

    app = Behavior.boot()
    app.add(Desk)

    def arm_and_copy() -> contextvars.Context:
        app.dispatch("desk.arm")
        return contextvars.copy_context()

    def append() -> None:
        app.continuations["paid"].args["items"].append("b")

    def parent_emit() -> str:
        app.emit("paid")
        return str(app.get("desk").seen)

    parent = contextvars.copy_context()
    child = parent.run(arm_and_copy)
    child.run(append)
    assert parent.run(parent_emit) == "a"
