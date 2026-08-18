"""Composition root.

Behavior is the single place product behavior is registered and turned into Ops.
"""

from __future__ import annotations

from typing import Any, Type


class Behavior:
    """Composition root for product behavior."""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._components: dict[str, Any] = {}

    @classmethod
    def boot(cls, title: str = "") -> "Behavior":
        """Create a root. Attaches live Document/Channel when available; otherwise in-process."""
        return cls(title=title)

    def add(self, component: Type[Any] | Any) -> None:
        """Register a Component class or instance."""
        if isinstance(component, type):
            inst = component()
        else:
            inst = component
        cid = getattr(inst, "id", None) or component.__name__
        self._components[str(cid)] = inst

    def components(self) -> dict[str, Any]:
        return dict(self._components)
