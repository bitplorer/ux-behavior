"""Host-only CustomEvent wire op.

Builds Channel ``{op: "dispatch"}``. Not a Behavior ``Op``. Not on the
frozen public surface. Classic ``ux-channel.js`` already applies this as
``CustomEvent`` on ``target`` (CSS selector) or ``document.body``.
"""

from __future__ import annotations

from typing import Any, Optional


def client_event(
    name: str,
    *,
    target: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
    bubbles: bool = True,
) -> dict:
    """Channel wire op. Host-only. Not a Behavior Op. Not public API."""
    name = str(name or "").strip()
    if not name:
        raise ValueError("client_event name must be non-empty")
    try:
        from ux_channel.protocol.ops import dispatch
    except ImportError:
        body: dict[str, Any] = {
            "op": "dispatch",
            "name": name,
            "bubbles": bubbles,
        }
        if target is not None:
            body["target"] = target
        if detail is not None:
            body["detail"] = detail
        return body
    return dispatch(name, target=target, detail=detail, bubbles=bubbles)
