"""Events and continuations.

Event = named signal.
Continuation = deferred action bound to that signal for a turn.

    follow_up("paid", "orders.confirm", order_id=1)
    # later
    app.emit("paid", order_id=1)
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

_pending: ContextVar[list["Continuation"] | None] = ContextVar(
    "ux_behavior_follow_ups", default=None
)


@dataclass
class Continuation:
    event: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    args_from: dict[str, str] = field(default_factory=dict)


def follow_up(
    event: str,
    action: str,
    *,
    args_from: dict[str, str] | None = None,
    **args: Any,
) -> Continuation:
    """Bind an event to a later action. Call only inside an @action.

    ``args`` are fixed now. ``args_from`` maps continuation arg ← emit slot.
    """
    event = str(event or "").strip()
    action = str(action or "").strip()
    if not event:
        raise ValueError("follow_up event must be non-empty")
    if "." not in action:
        raise ValueError(
            f"follow_up action must be 'component.method', got {action!r}"
        )
    item = Continuation(
        event=event,
        action=action,
        args=dict(args),
        args_from=dict(args_from or {}),
    )
    bucket = _pending.get()
    if bucket is None:
        raise RuntimeError(
            "follow_up() only works during Behavior.dispatch of an @action"
        )
    bucket.append(item)
    return item


def _begin_follow_ups() -> Any:
    token = _pending.set([])
    return token


def _end_follow_ups(token: Any) -> list[Continuation]:
    bucket = list(_pending.get() or [])
    _pending.reset(token)
    return bucket
