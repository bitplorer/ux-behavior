"""@action — mark a method as product behavior that produces Ops."""

from __future__ import annotations

from typing import Any, Callable

from ux_behavior.ops import Op


def action(
    fn: Callable[..., Any] | None = None,
    *,
    caps: tuple[str, ...] | list[str] = (),
) -> Any:
    """Decorator. Caps required unless explicitly ``caps=()`` (public opt-out).

    Return contract (enforced at call time):

    - ``None`` — ok (state mutation; runtime may project dirty fields)
    - ``list[Op]`` — ok
    - single ``Op`` — normalized to ``[Op]``
    - anything else — ``TypeError``
    """

    def deco(f: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> list[Op] | None:
            result = f(*args, **kwargs)
            if result is None:
                return None
            if isinstance(result, Op):
                return [result]
            if isinstance(result, list):
                bad = [item for item in result if not isinstance(item, Op)]
                if bad:
                    raise TypeError(
                        f"@action {f.__qualname__} must return list[Op] | Op | None; "
                        f"list contained {type(bad[0]).__name__}"
                    )
                return result
            raise TypeError(
                f"@action {f.__qualname__} must return list[Op] | Op | None, "
                f"got {type(result).__name__}"
            )

        setattr(wrapped, "_ux_behavior_action", True)
        setattr(wrapped, "_ux_behavior_caps", tuple(caps))
        setattr(wrapped, "__name__", getattr(f, "__name__", "action"))
        setattr(wrapped, "__qualname__", getattr(f, "__qualname__", "action"))
        setattr(wrapped, "__doc__", f.__doc__)
        return wrapped

    if fn is not None:
        return deco(fn)
    return deco
