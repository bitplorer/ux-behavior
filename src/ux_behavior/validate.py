"""Action argument binding and light type checks."""

from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin

from ux_behavior.errors import ValidationError


def bind_action_args(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Bind kwargs to the action signature (method already bound — no self)."""
    sig = inspect.signature(fn)
    try:
        bound = sig.bind_partial(**kwargs)
        bound.apply_defaults()
    except TypeError as exc:
        raise ValidationError(str(exc), fields={"_": str(exc)}) from exc

    out = dict(bound.arguments)
    errors: dict[str, str] = {}

    for name, param in sig.parameters.items():
        if name not in out:
            if param.default is inspect.Parameter.empty and param.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                errors[name] = "required"
            continue
        if name not in out:
            continue
        ann = param.annotation
        if ann is inspect.Parameter.empty:
            continue
        val = out[name]
        if not _matches(ann, val):
            errors[name] = f"expected {_ann_name(ann)}, got {type(val).__name__}"

    if errors:
        raise ValidationError("invalid action arguments", fields=errors)
    return out


def _ann_name(ann: Any) -> str:
    return getattr(ann, "__name__", str(ann))


def _matches(ann: Any, value: Any) -> bool:
    origin = get_origin(ann)
    if origin is None:
        if ann is Any:
            return True
        if isinstance(ann, type):
            return type(value) is ann or isinstance(value, ann)
        return True
    # Optional / Union
    args = get_args(ann)
    if type(None) in args:
        if value is None:
            return True
        return any(_matches(a, value) for a in args if a is not type(None))
    return True
