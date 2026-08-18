"""Elevated Result builder.

Hosts prefer this over hand-rolling lower + compose.
Still lives under the progressive wire door — not on top-level __all__.

Example::

    ops = (
        Result()
        .morph("#view", html)
        .motion(scene.play())   # must not inject html on #view
        .navigate("/cart")
        .build()
    )
"""

from __future__ import annotations

from typing import Any

from ux_behavior.wire.compose import Conflict, compose, lower


class Result:
    """Build a Channel-shaped ops list with XOR and navigate-last enforced."""

    def __init__(self) -> None:
        self._items: list[Any] = []

    def morph(self, target: str, html: Any = "") -> "Result":
        """Authority morph (projects to idiomorph at the wire door)."""
        self._items.append(lower(target, html))
        return self

    def motion(self, scene_or_ops: Any) -> "Result":
        """Fold a Scene or transition ops. Must not also inject html on a morph target."""
        self._items.append(scene_or_ops)
        return self

    def navigate(self, href: str) -> "Result":
        """Navigate — ordered last at compose time."""
        self._items.append({"op": "navigate", "href": href})
        return self

    def notify(self, message: str, *, level: str = "info") -> "Result":
        """S-only log notice on the Result."""
        self._items.append(
            {"op": "log.append", "message": message, "level": level}
        )
        return self

    def op(self, item: Any) -> "Result":
        """Append any foldable item (wire dict, Op, Scene, list)."""
        self._items.append(item)
        return self

    def build(self) -> list[dict[str, Any]]:
        """Compose and return the final ops list.

        Raises:
            Conflict: morph(T) XOR scene.enter(T, html=) on the same Result.
        """
        return compose(*self._items)

    def explain(self) -> list[dict[str, Any]]:
        """Alias of build() for dry-run readability at call sites."""
        return self.build()
