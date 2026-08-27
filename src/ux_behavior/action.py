"""@action — mark a method as product behavior that produces Ops.

Also provides fail-closed UI binding:

    **self.add.ui(sku="tee")     # preferred author path
    **bind(self.add, sku="tee")  # generic helper

Invoke stays normal::

    self.add(sku="tee")
"""

from __future__ import annotations

import functools
import inspect
import json
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


def _is_action(obj: Any) -> bool:
    if obj is None:
        return False
    if isinstance(obj, (ActionMethod, BoundAction)):
        return True
    if getattr(obj, "_ux_behavior_action", False):
        return True
    fn = getattr(obj, "__func__", None)
    if fn is not None and getattr(fn, "_ux_behavior_action", False):
        return True
    return False


def _unwrap_action_fn(obj: Any) -> Callable[..., Any]:
    """Return the underlying decorated function."""
    if isinstance(obj, BoundAction):
        return obj._action._fn
    if isinstance(obj, ActionMethod):
        return obj._fn
    fn = getattr(obj, "__func__", None)
    if callable(fn) and getattr(fn, "_ux_behavior_action", False):
        return fn
    if callable(obj) and getattr(obj, "_ux_behavior_action", False):
        return obj  # type: ignore[return-value]
    raise TypeError(
        f"expected an @action method, got {type(obj).__name__}"
    )


def _action_instance(obj: Any) -> Any | None:
    if isinstance(obj, BoundAction):
        return obj._instance
    return getattr(obj, "__self__", None)


def _action_verb_name(fn: Callable[..., Any], instance: Any | None) -> str:
    """Derive channel/progressive action name: {id}.{method} or method."""
    method = getattr(fn, "__name__", "action")
    if instance is not None:
        sid = getattr(instance, "id", None)
        if isinstance(sid, str) and sid.strip():
            return f"{sid.strip()}.{method}"
        cls = type(instance)
        return f"{cls.__name__}.{method}"
    # Unbound: Class.method from qualname when possible
    qn = getattr(fn, "__qualname__", "") or ""
    if "." in qn:
        owner, _, _name = qn.rpartition(".")
        if owner and "<" not in owner:
            return f"{owner}.{method}"
    return method


def _validate_ui_kwargs(fn: Callable[..., Any], kwargs: dict[str, Any]) -> None:
    """Fail closed: kwargs must be parameters of the action (excluding self/cls)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return
    params = sig.parameters
    # Accept **kwargs on the action as open-ended
    has_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
    )
    allowed: set[str] = set()
    for name, p in params.items():
        if name in ("self", "cls"):
            continue
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            allowed.add(name)
    if has_var_kw:
        return
    unknown = set(kwargs) - allowed
    if unknown:
        bad = ", ".join(sorted(unknown))
        raise TypeError(
            f"@action {getattr(fn, '__qualname__', fn)!s} ui/bind "
            f"got unexpected kwarg(s): {bad}"
        )


def action_ui_attrs(
    action_obj: Any,
    *,
    _instance: Any | None = None,
    **kwargs: Any,
) -> dict[str, str]:
    """Build progressive control attrs for an @action callable.

    Fail-closed: non-actions and unknown kwargs raise TypeError.
    Emits both families: ``data-ux-action`` (progressive) and
    ``data-channel-action`` (live synthesizer). No ux_channel import —
    the attr names are the documented triad, not a wire dependency.
    """
    if not _is_action(action_obj):
        raise TypeError(
            f"ui/bind requires an @action method, got {type(action_obj).__name__}"
        )
    fn = _unwrap_action_fn(action_obj)
    instance = _instance if _instance is not None else _action_instance(action_obj)
    _validate_ui_kwargs(fn, kwargs)
    verb = _action_verb_name(fn, instance)
    attrs: dict[str, str] = {
        "data-ux-action": verb,
        "data-channel-action": verb,
    }
    if kwargs:
        attrs["data-channel-args"] = json.dumps(
            {k: str(v) for k, v in kwargs.items()},
            separators=(",", ":"),
            ensure_ascii=True,
        )
    for k, v in kwargs.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def bind(action_obj: Any, **kwargs: Any) -> dict[str, str]:
    """Generic helper: ``**bind(self.add, sku=\"tee\")``.

    Same fail-closed rules as ``action.ui``.
    """
    return action_ui_attrs(action_obj, **kwargs)


class BoundAction:
    """Instance-bound @action: callable + ``.ui(**kwargs)``."""

    __slots__ = ("_action", "_instance")

    def __init__(self, action: "ActionMethod", instance: Any) -> None:
        self._action = action
        self._instance = instance

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._action(*args, _bound_instance=self._instance, **kwargs)

    def ui(self, **kwargs: Any) -> dict[str, str]:
        """DOM-ready progressive attrs for this action + args."""
        return action_ui_attrs(self, **kwargs)

    @property
    def __func__(self) -> Callable[..., Any]:
        return self._action._fn

    @property
    def __self__(self) -> Any:
        return self._instance

    def __repr__(self) -> str:
        return f"<BoundAction {self._action._qualname} of {self._instance!r}>"

    def __getattr__(self, name: str) -> Any:
        # Expose markers for registry introspection
        if name.startswith("_ux_behavior_"):
            return getattr(self._action, name)
        raise AttributeError(name)


class ActionMethod:
    """Descriptor returned by @action: supports invoke + ``.ui``."""

    def __init__(
        self,
        fn: Callable[..., Any],
        *,
        caps: tuple[str, ...],
        is_async: bool,
        qualname: str,
    ) -> None:
        self._fn = fn
        self._caps = caps
        self._is_async = is_async
        self._qualname = qualname
        functools.update_wrapper(self, fn)
        self._ux_behavior_action = True
        self._ux_behavior_caps = caps
        self._ux_behavior_async = is_async

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return BoundAction(self, obj)

    def __call__(
        self, *args: Any, _bound_instance: Any | None = None, **kwargs: Any
    ) -> Any:
        if self._is_async:

            async def _run() -> list[Op] | None:
                if _bound_instance is not None:
                    result = await self._fn(_bound_instance, *args, **kwargs)
                else:
                    result = await self._fn(*args, **kwargs)
                return _normalize_result(result, self._qualname)

            return _run()

        if _bound_instance is not None:
            result = self._fn(_bound_instance, *args, **kwargs)
        else:
            result = self._fn(*args, **kwargs)
        return _normalize_result(result, self._qualname)

    def ui(self, **kwargs: Any) -> dict[str, str]:
        """Unbound UI attrs (verb from qualname; prefer bound ``.ui``)."""
        return action_ui_attrs(self, **kwargs)

    def __repr__(self) -> str:
        return f"<ActionMethod {self._qualname}>"


def action(
    fn: Callable[..., Any] | None = None,
    *,
    caps: tuple[str, ...] | list[str] = (),
) -> Any:
    """Decorator. Caps required unless ``caps=()`` (public).

    Supports sync and async methods. Return: None | Op | list[Op].
    Nested list[Op] from chrome macros is flattened one level.

    UI binding (fail-closed)::

        button("+", **self.add.ui(sku="tee"))
        button("+", **bind(self.add, sku="tee"))
    """

    def deco(f: Callable[..., Any]) -> ActionMethod:
        qualname = getattr(f, "__qualname__", "action")
        is_async = inspect.iscoroutinefunction(f)
        return ActionMethod(
            f,
            caps=tuple(caps),
            is_async=is_async,
            qualname=qualname,
        )

    if fn is not None:
        return deco(fn)
    return deco
