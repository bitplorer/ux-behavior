"""Fold author items into one Channel-shaped ops list.

Law on one Result: morph(T) XOR scene.enter(T, html=…).
Navigate kinds ordered last.
Speaks wire shape only — never loads the Channel package.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ux_behavior.ops import Op

_NAV = frozenset({"navigate", "push_url", "reload", "push"})
_MORPH = frozenset({"morph", "swap"})


class Conflict(ValueError):
    """morph(T) and motion html for T on the same Result."""


def as_selector(target: str) -> str:
    text = str(target).strip()
    if not text:
        raise ValueError("morph target is empty")
    if text[0] in "#.[:*":
        return text
    return f"#{text}"


def lower(target: str, html: Any = "") -> dict[str, Any]:
    """Author morph → Channel idiomorph wire shape."""
    sel = as_selector(target)
    return {
        "op": "morph",
        "target": sel,
        "html": html,
        "morph": "idiomorph",
    }


def compose(*items: Any) -> list[dict[str, Any]]:
    """Flatten items to Channel-shaped ops. Reject overlapping writes."""
    ops: list[dict[str, Any]] = []
    for item in items:
        ops.extend(_flatten(item))
    _reject_overlap(ops)
    return _order(ops)


def _flatten(item: Any) -> list[dict[str, Any]]:
    if item is None:
        return []
    if isinstance(item, dict):
        return [item]
    if isinstance(item, Op):
        if item.pair != ("ui.dom", "morph"):
            raise TypeError(
                f"compose() only lowers ui.dom.morph Ops, got {item.fq}. "
                "Pass a wire dict or a Scene."
            )
        return [lower(item.payload.get("target") or "", item.payload.get("patch") or "")]
    if isinstance(item, (list, tuple)):
        out: list[dict[str, Any]] = []
        for child in item:
            out.extend(_flatten(child))
        return out
    play = getattr(item, "play", None)
    if callable(play):
        result = play()
        if isinstance(result, Mapping) and isinstance(result.get("ops"), list):
            return [op for op in result["ops"] if isinstance(op, dict)]
    ops_fn = getattr(item, "ops", None)
    if callable(ops_fn):
        produced = ops_fn()
        if isinstance(produced, Iterable):
            return [op for op in produced if isinstance(op, dict)]
    raise TypeError(
        f"compose() cannot fold {type(item).__name__}. "
        "Pass a wire dict, ui.dom.morph Op, Scene, or list of those."
    )


def _order(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    head = [op for op in ops if op.get("op") not in _NAV]
    tail = [op for op in ops if op.get("op") in _NAV]
    return head + tail


def _reject_overlap(ops: list[dict[str, Any]]) -> None:
    morphs: set[str] = set()
    motion_html: set[str] = set()
    for op in ops:
        kind = str(op.get("op") or "")
        if kind in _MORPH and op.get("target"):
            morphs.add(as_selector(str(op["target"])))
        if kind.startswith("transition."):
            motion_html.update(_html_targets(op.get("plan")))
    clash = morphs & motion_html
    if clash:
        shown = ", ".join(sorted(clash))
        raise Conflict(
            f"morph({shown}) XOR scene.enter({shown}, html=) on one Result. "
            "Morph the slot, or let motion inject html — not both."
        )


def _html_targets(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, Mapping):
        html = node.get("html")
        target = node.get("target")
        if html not in (None, "") and target:
            found.add(as_selector(str(target)))
        for value in node.values():
            found.update(_html_targets(value))
    elif isinstance(node, (list, tuple)):
        for child in node:
            found.update(_html_targets(child))
    return found
