"""Composition root.

Behavior is the single place product behavior is registered and turned into Ops.
"""

from __future__ import annotations

from typing import Any, Type

from ux_behavior.ops import Op, update


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
        cid = getattr(inst, "id", None) or getattr(component, "__name__", "component")
        self._components[str(cid)] = inst

    def components(self) -> dict[str, Any]:
        return dict(self._components)

    def get(self, component_id: str) -> Any:
        """Return a registered component by id."""
        try:
            return self._components[component_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._components)) or "(none)"
            raise KeyError(
                f"unknown component id {component_id!r}. registered: {known}"
            ) from exc

    def refresh(self, component_id: str) -> list[Op]:
        """Re-render a registered component into an authority morph Op.

        Requires the Root to own the id → instance registry (via ``add``).
        Hosts use this instead of hand-building morph dicts for a known region.
        """
        inst = self.get(component_id)
        render = getattr(inst, "render", None)
        if not callable(render):
            raise TypeError(
                f"component {component_id!r} has no callable render()"
            )
        html = render()
        return [update(component_id, html)]
