"""Action argument binding and light type checks.

The product signature is the @action function (self skipped). Envelope keys
from Channel Intent (``args=dict``) and BoundAction's ``__call__(*args, **kwargs)``
are not product parameters. ``apply_defaults`` filling VAR_POSITIONAL as
``args=()`` is how ``tick() got an unexpected keyword argument 'args'`` leaked.
"""

from __future__ import annotations

import inspect
from typing import Any, ForwardRef, get_args, get_origin

from ux_behavior.errors import ValidationError

_UNRESOLVED = object()


def _bind_target(fn: Any) -> Any:
    """Underlying @action function. BoundAction.__call__(*args) is not it."""
    action = getattr(fn, "_action", None)
    inner = getattr(action, "_fn", None) if action is not None else None
    if callable(inner):
        return inner
    inner = getattr(fn, "_fn", None)
    if callable(inner):
        return inner
    inner = getattr(fn, "__func__", None)
    if callable(inner):
        return inner
    return fn


def _product_signature(fn: Any) -> inspect.Signature:
    """Signature authors wrote, without self/cls."""
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    if params and params[0].name in ("self", "cls") and params[0].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ):
        return sig.replace(parameters=params[1:])
    return sig


def _unpack_intent_args(sig: inspect.Signature, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Flatten Channel-style ``args=dict`` unless the action declares ``args``."""
    packed = kwargs.get("args")
    if not isinstance(packed, dict):
        return dict(kwargs)
    if "args" in sig.parameters:
        param = sig.parameters["args"]
        if param.kind not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            return dict(kwargs)
    out = dict(packed)
    for key, value in kwargs.items():
        if key == "args":
            continue
        out[key] = value
    return out


def bind_action_args(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Bind kwargs to the action signature (method already bound — no self)."""
    target = _bind_target(fn)
    sig = _product_signature(target)
    kwargs = _unpack_intent_args(sig, dict(kwargs))
    provided = set(kwargs)
    try:
        bound = sig.bind_partial(**kwargs)
        bound.apply_defaults()
    except TypeError as exc:
        raise ValidationError(str(exc), fields={"_": str(exc)}) from exc

    out: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for name, param in sig.parameters.items():
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            continue
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            extra = bound.arguments.get(name) or {}
            if isinstance(extra, dict):
                out.update(extra)
            continue
        if name not in bound.arguments:
            if param.default is inspect.Parameter.empty:
                errors[name] = "required"
            continue
        out[name] = bound.arguments[name]
        if name not in provided:
            continue
        ann = _resolve_annotation(target, param.annotation)
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


def _resolve_annotation(fn: Any, ann: Any) -> Any:
    """Resolve one parameter hint. A failure leaves the others in force."""
    if ann is inspect.Parameter.empty or not isinstance(ann, str):
        return ann
    globalns = getattr(fn, "__globals__", {})
    resolved = _evaluate_annotation(globalns, ann)
    if resolved is _UNRESOLVED:
        return ann
    return resolved


def _evaluate_annotation(globalns: dict[str, Any], expr: str) -> Any:
    try:
        value = ForwardRef(expr).evaluate(
            globals=globalns,
            locals=None,
            type_params=None,
        )
    except Exception:
        return _UNRESOLVED
    # A quoted forward ref evaluates to a string. Resolve that name too,
    # the same second step get_type_hints does, but only for this parameter.
    if isinstance(value, str):
        try:
            value = ForwardRef(value).evaluate(
                globals=globalns,
                locals=None,
                type_params=None,
            )
        except Exception:
            return _UNRESOLVED
    return value


def _matches(ann: Any, value: Any) -> bool:
    if isinstance(ann, str):
        return True  # unresolved forward ref — skip
    origin = get_origin(ann)
    if origin is None:
        if ann is Any:
            return True
        if isinstance(ann, type):
            return isinstance(value, ann)
        return True
    args = get_args(ann)
    if type(None) in args:
        if value is None:
            return True
        return any(_matches(a, value) for a in args if a is not type(None))
    return True
