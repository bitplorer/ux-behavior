"""Control attrs for HTMX / Channel (progressive door).

When Behavior is attached, mint via Channel.
When offline, return plain data-action attrs (Host may add Cap later).
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable

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


def control_attrs(
    behavior: Any,
    action: Any,
    **args: Any,
) -> dict[str, str]:
    """Mint control attributes for a product action.

    Live: Channel ``wire.control`` when attached.
    Offline: ``data_action`` + JSON args (no Cap token).
    """
    action_name = resolve_action_name(behavior, action)
    wire = getattr(behavior, "_wire", None)
    dispatch = getattr(behavior, "_dispatch", None)
    if wire is not None and dispatch is not None:
        trust: dict[str, Any] = {
            k: v for k, v in args.items() if k != UX_ACTION_KEY
        }
        trust[UX_ACTION_KEY] = action_name
        try:
            return wire.control(dispatch, trust=trust).as_ux_dom()
        except Exception:
            pass
    payload = {k: v for k, v in args.items() if k != UX_ACTION_KEY}
    return {
        "data_action": action_name,
        "data_args": json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ),
    }
