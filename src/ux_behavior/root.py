"""Composition root.

Behavior is the single place product behavior is registered and turned into Ops.
"""

from __future__ import annotations

import importlib.util
from typing import Any, Callable, Iterable, Type

from ux_behavior.domains import DomainTable, default_table
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

    def __init__(self, title: str = "", domains: DomainTable | None = None) -> None:
        self.title = title
        self._components: dict[str, Any] = {}
        self.domains = domains or default_table()
        self._cores_available: dict[str, bool] = {
            "ux_dom": False,
            "ux_channel": False,
        }
        self._wire: Any = None
        self._region_render: Callable[[], Any] | None = None
        self._region_uid: str | None = None

    @classmethod
    def boot(cls, title: str = "") -> "Behavior":
        """Create a root. Soft-detects live cores without importing them."""
        root = cls(title=title)
        root._cores_available = {
            "ux_dom": importlib.util.find_spec("ux_dom") is not None,
            "ux_channel": importlib.util.find_spec("ux_channel") is not None,
        }
        return root

    @property
    def cores_available(self) -> dict[str, bool]:
        return dict(self._cores_available)

    @property
    def stamp(self) -> frozenset[tuple[str, str]]:
        return self.domains.stamp

    def use(self, *names: str) -> "Behavior":
        self.domains.use(*names)
        return self

    def domain(
        self,
        name: str,
        version: str,
        pairs: Iterable[tuple[str, str]],
    ) -> "Behavior":
        self.domains.domain(name, version, pairs)
        return self

    def region(self, render: Callable[[], Any], *, uid: str | None = None) -> "Behavior":
        """Register the Host paint callback for live Channel region attach."""
        self._region_render = render
        if uid:
            self._region_uid = uid
        return self

    def attach(self, asgi: Any, **kwargs: Any) -> Any:
        """Mount live Channel behind this Behavior (via the wire door)."""
        from ux_behavior.wire.attach import attach as attach_wire

        return attach_wire(self, asgi, **kwargs)

    def add(self, component: Type[Any] | Any) -> Any:
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
        try:
            return self._components[component_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._components)) or "(none)"
            raise KeyError(
                f"unknown component id {component_id!r}. registered: {known}"
            ) from exc

    def refresh(self, component_id: str) -> list[Op]:
        inst = self.get(component_id)
        render = getattr(inst, "render", None)
        if not callable(render):
            raise TypeError(
                f"component {component_id!r} has no callable render()"
            )
        html = render()
        return [update(component_id, html)]

    def actions(self, component_id: str | None = None) -> list[str]:
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
                ops = self.refresh(component_id)
            else:
                ops = []
        elif isinstance(result, list):
            ops = result
        else:
            raise TypeError(
                f"{action!r} returned {type(result).__name__}; "
                "expected list[Op] | None"
            )

        self._check_stamp(ops)
        return ops

    def _check_stamp(self, ops: list[Op]) -> None:
        for op in ops:
            if not isinstance(op, Op):
                raise TypeError(f"expected Op, got {type(op).__name__}")
            if not self.domains.allows(*op.pair):
                raise PermissionError(
                    f"pair {op.fq} is not on the session stamp"
                )
