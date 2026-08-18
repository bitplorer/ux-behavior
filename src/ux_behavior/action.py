"""@action — mark a method as product behavior that produces Ops."""

from __future__ import annotations

from typing import Any, Callable


def action(fn: Callable[..., Any] | None = None, *, caps: tuple[str, ...] | list[str] = ()) -> Any:
    """Decorator. Caps required unless explicitly ``caps=()`` (public opt-out).

    The decorated method is expected to return ``list[Op]`` or mutate
    component state that is later projected to updates.
    """

    def deco(f: Callable[..., Any]) -> Callable[..., Any]:
        setattr(f, "_ux_behavior_action", True)
        setattr(f, "_ux_behavior_caps", tuple(caps))
        return f

    if fn is not None:
        return deco(fn)
    return deco
