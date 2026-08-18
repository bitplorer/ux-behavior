"""Composition root.

Behavior is the single place product behavior is registered and turned into Ops.
"""

from __future__ import annotations

import importlib.util
from typing import Any, Type

from ux_behavior.ops import Op, update


def _public_state(inst: Any) -> dict[str, Any]:
    """Snapshot of author-visible instance fields (not methods / privates)."""
    out: dict[str, Any] = {}
    for key, value in vars(inst).items():
        if key.startswith("_"):
            continue
        out[key] = value
    return out


class Behavior:
    """Composition root for product behavior."""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._components: dict[str, Any] = {}
        self._cores_available: dict[str, bool] = {
            "ux_dom": False,
            "ux_channel": False,
        }

    @classmethod
    def boot(cls, title: str = "") -> "Behavior":
        """Create a root. Soft-detects live cores without importing them.

        Document/Channel attach stays behind the progressive wire door.
        Cold import of this package never loads cores.
        """
        root = cls(title=title)
        root._cores_available = {
            "ux_dom": importlib.util.find_spec("ux_dom") is not None,
            "ux_channel": importlib.util.find_spec("ux_channel") is not None,
        }
        return root

    @property
    def cores_available(self) -> dict[str, bool]:
        return dict(self._cores_available)

    def add(self, component: Type[Any] | Any) -> Any:
        """Register a Component class or instance."""
        if isinstance(component, type):
            inst = component()
        else:
            inst = component
        cid = getattr(inst, "id", None) or getattr(component, "__name__", "component")
        cid = str(cid)
        if not cid:
            raise ValueError("component id must be a non-empty string")
        self._components[cid] = inst
        return inst

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
        """Re-render a registered component into an authority morph Op."""
        inst = self.get(component_id)
        render = getattr(inst, "render", None)
        if not callable(render):
            raise TypeError(
                f"component {component_id!r} has no callable render()"
            )
        html = render()
        return [update(component_id, html)]

    def actions(self, component_id: str | None = None) -> list[str]:
        """Qualified action names (``id.method``)."""
        names: list[str] = []
        items = (
            {component_id: self.get(component_id)}
            if component_id is not None
            else self._components
        )
        for cid, inst in items.items():
            for name in dir(inst):
                if name.startswith("_"):
                    continue
                attr = getattr(inst, name, None)
                if callable(attr) and getattr(attr, "_ux_behavior_action", False):
                    names.append(f"{cid}.{name}")
        return sorted(names)

    def dispatch(self, action: str, **kwargs: Any) -> list[Op]:
        """Run ``component.method`` and return Ops.

        Action name form: ``"cart.badge.add"`` (component id + method).

        Return handling:

        - explicit ``list[Op]`` / ``Op`` → used as-is (Op normalized by @action)
        - ``None`` → if public fields changed, project ``refresh(component_id)``
        - ``None`` + no field changes → ``[]``

        Caps metadata is recorded on the callable; live Cap verify stays in Channel.
        """
        if "." not in action:
            raise ValueError(
                f"action name must be 'component.method', got {action!r}"
            )
        component_id, method = action.rsplit(".", 1)
        inst = self.get(component_id)
        fn = getattr(inst, method, None)
        if fn is None or not callable(fn):
            raise AttributeError(f"unknown action {action!r}")
        if not getattr(fn, "_ux_behavior_action", False):
            raise TypeError(f"{action!r} is not marked with @action")

        before = _public_state(inst)
        result = fn(**kwargs)

        if result is None:
            after = _public_state(inst)
            if after != before:
                return self.refresh(component_id)
            return []

        if isinstance(result, list):
            return result

        raise TypeError(
            f"{action!r} returned {type(result).__name__}; "
            "expected list[Op] | None"
        )
