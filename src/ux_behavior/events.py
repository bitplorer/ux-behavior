"""Events and continuations.

Event = named signal.
Continuation = deferred action bound to that signal for a turn.

    follow_up("paid", "orders.confirm", order_id=1)
    # later
    app.emit("paid", order_id=1)
"""

from __future__ import annotations

import copy
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any
from weakref import WeakKeyDictionary

_pending: ContextVar[list["Continuation"] | None] = ContextVar(
    "ux_behavior_follow_ups", default=None
)
# Armed continuations, per contextvars context, then per Behavior scope.
# Keys are weak. A collected Behavior drops its scope and its args.
# Each write or read installs a new bag in this context, with new Continuation objects.
_armed: ContextVar[WeakKeyDictionary | None] = ContextVar(
    "ux_behavior_armed_continuations", default=None
)


class _ContinuationScope:
    """Identity for one Behavior's armed table. Weak-key, not a bare object()."""

    __slots__ = ("__weakref__",)


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


def _copy_value(value: Any) -> Any:
    """Deep copy one mapping value.

    If ``deepcopy`` raises, the original value is returned and stays shared
    with the source continuation.
    """
    try:
        return copy.deepcopy(value)
    except Exception:
        return value


def _copy_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: _copy_value(value) for key, value in mapping.items()}


def _clone_continuation(item: Continuation) -> Continuation:
    """New Continuation. Each ``args`` and ``args_from`` value is deep-copied.

    A value that ``copy.deepcopy`` cannot copy stays shared with ``item``.
    """
    return Continuation(
        event=item.event,
        action=item.action,
        args=_copy_mapping(item.args),
        args_from=_copy_mapping(item.args_from),
    )


def _copy_bag(bag: WeakKeyDictionary | None) -> WeakKeyDictionary:
    """Weak copy. Each Continuation belongs to the destination bag only."""
    copied: WeakKeyDictionary = WeakKeyDictionary()
    if not bag:
        return copied
    for key, table in list(bag.items()):
        copied[key] = {
            event: _clone_continuation(item) for event, item in table.items()
        }
    return copied


def _local_bag() -> WeakKeyDictionary | None:
    """Install this context's own bag so a copied context does not share objects."""
    bag = _armed.get()
    if not bag:
        return None
    local = _copy_bag(bag)
    _armed.set(local)
    return local


def _armed_continuations(scope: object) -> dict[str, Continuation]:
    """Continuations armed in this context for one Behavior scope."""
    bag = _local_bag()
    if not bag:
        return {}
    return dict(bag.get(scope) or {})


def _arm_continuation(scope: object, item: Continuation) -> None:
    """Store a copy of ``item`` for this context only. Parent bags stay put."""
    new_bag = _copy_bag(_armed.get())
    table = dict(new_bag.get(scope) or {})
    table[item.event] = _clone_continuation(item)
    new_bag[scope] = table
    _armed.set(new_bag)


def _begin_follow_ups() -> Any:
    token = _pending.set([])
    return token


def _end_follow_ups(token: Any) -> list[Continuation]:
    bucket = list(_pending.get() or [])
    _pending.reset(token)
    return bucket
