"""Control attrs for HTMX / Channel (progressive door).

Live mint failure is never silent: diagnostics.warn then offline attrs,
or raise when behavior.strict_control is True.
"""

from __future__ import annotations

import inspect
import json
from typing import Any

from ux_behavior.wire.attach import UX_ACTION_KEY


def resolve_action_name(behavior: Any, action: Any) -> str:
    if isinstance(action, str):
        return action
    if not callable(action):
        raise TypeError(f"control target is not callable: {type(action).__name__}")
    if inspect.ismethod(action):
        ident = getattr(action.__self__, "id", None)
        if ident:
            return f"{ident}.{action.__name__}"
    name = getattr(action, "__name__", None)
    if name:
        return str(name)
    raise TypeError("cannot resolve action name for control()")


def _offline_attrs(action_name: str, args: dict[str, Any]) -> dict[str, str]:
    payload = {k: v for k, v in args.items() if k != UX_ACTION_KEY}
    return {
        "data_action": action_name,
        "data_args": json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ),
        "data_cap": "",
    }


def control_attrs(
    behavior: Any,
    action: Any,
    **args: Any,
) -> dict[str, str]:
    action_name = resolve_action_name(behavior, action)
    wire = getattr(behavior, "_wire", None)
    dispatch = getattr(behavior, "_dispatch", None)
    diag = getattr(behavior, "diagnostics", None)

    if wire is None:
        if diag is not None:
            diag.warn(
                "CONTROL_OFFLINE",
                "control() without Channel — no Cap token",
                action=action_name,
            )
        return _offline_attrs(action_name, args)

    if dispatch is None:
        if diag is not None:
            diag.error(
                "CONTROL_NO_DISPATCH",
                "wire present but dispatch handler missing",
                action=action_name,
            )
        if getattr(behavior, "strict_control", False):
            raise RuntimeError("control() requires wire dispatch handler")
        return _offline_attrs(action_name, args)

    trust: dict[str, Any] = {k: v for k, v in args.items() if k != UX_ACTION_KEY}
    trust[UX_ACTION_KEY] = action_name
    try:
        attrs = wire.control(dispatch, trust=trust).as_ux_dom()
        if diag is not None:
            diag.info("CONTROL_MINTED", "Cap control attrs minted", action=action_name)
        return attrs
    except Exception as exc:
        if diag is not None:
            diag.error(
                "CONTROL_MINT_FAILED",
                f"Channel control mint failed: {exc}",
                action=action_name,
                error=type(exc).__name__,
            )
        if getattr(behavior, "strict_control", False):
            raise
        if diag is not None:
            diag.warn(
                "CONTROL_FALLBACK_OFFLINE",
                "falling back to offline control attrs (no Cap)",
                action=action_name,
            )
        return _offline_attrs(action_name, args)
