"""@action — mark a method as product behavior that produces Ops."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

from ux_behavior.ops import Op


def _normalize_result(result: Any, qualname: str) -> list[Op] | None:
    if result is None:
        return None
    if isinstance(result, Op):
        return [result]
    if isinstance(result, list):
        flat: list[Op] = []
        for item in result:
            if isinstance(item, Op):
                flat.append(item)
            elif isinstance(item, list):
                # chrome macros return list[Op]; allow return [open(...), notify(...)]
                for sub in item:
                    if not isinstance(sub, Op):
                        raise TypeError(
                            f"@action {qualname} must return list[Op] | Op | None; "
                            f"nested list contained {type(sub).__name__}"
                        )
                    flat.append(sub)
            else:
                raise TypeError(
                    f"@action {qualname} must return list[Op] | Op | None; "
                    f"list contained {type(item).__name__}"
                )
        return flat
    raise TypeError(
        f"@action {qualname} must return list[Op] | Op | None, "
        f"got {type(result).__name__}"
    )


def action(
    fn: Callable[..., Any] | None = None,
    *,
    caps: tuple[str, ...] | list[str] = (),
) -> Any:
    """Decorator. Caps required unless ``caps=()`` (public).

    Supports sync and async methods. Return: None | Op | list[Op].
    Nested list[Op] from chrome macros is flattened one level.
    """

    def deco(f: Callable[..., Any]) -> Callable[..., Any]:
        qualname = getattr(f, "__qualname__", "action")
        is_async = inspect.iscoroutinefunction(f)

        if is_async:

            @functools.wraps(f)
            async def wrapped(*args: Any, **kwargs: Any) -> list[Op] | None:
                result = await f(*args, **kwargs)
                return _normalize_result(result, qualname)

        else:

            @functools.wraps(f)
            def wrapped(*args: Any, **kwargs: Any) -> list[Op] | None:
                result = f(*args, **kwargs)
                return _normalize_result(result, qualname)

        setattr(wrapped, "_ux_behavior_action", True)
        setattr(wrapped, "_ux_behavior_caps", tuple(caps))
        setattr(wrapped, "_ux_behavior_async", is_async)
        return wrapped

    if fn is not None:
        return deco(fn)
    return deco
