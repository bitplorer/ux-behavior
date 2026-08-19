"""Composition root."""

from __future__ import annotations

import importlib.util
from typing import Any, Callable, Iterable, Type

from ux_behavior.domains import DomainTable, default_table
from ux_behavior.fields import (
    Field,
    client_field_names,
    plane_storage_key,
    transient_field_names,
)
from ux_behavior.ops import Op, update
from ux_behavior.planes import MISSING, MemoryPlanes, PlaneBackend


def _public_state(inst: Any) -> dict[str, Any]:
    """Dirty snapshot: skip TransientState and ClientState (ux-app parity)."""
    skip = transient_field_names(inst) | client_field_names(inst)
    out: dict[str, Any] = {}
    for key, value in vars(inst).items():
        if key.startswith("_"):
            continue
        if key in skip:
            continue
        out[key] = value
    return out


class Behavior:
    def __init__(self, title: str = "", domains: DomainTable | None = None) -> None:
        self.title = title
        self._components: dict[str, Any] = {}
        self.domains = domains or default_table()
        self.planes = MemoryPlanes()
        self._plane_overrides: dict[str, PlaneBackend] = {}
        self._plane_host_locked: set[str] = set()
        self._plane_channel_report: dict[str, str] = {}
        self._cores_available: dict[str, bool] = {
            "ux_dom": False,
            "ux_channel": False,
        }
        self._wire: Any = None
        self._region_render: Callable[[], Any] | None = None
        self._region_uid: str | None = None

    @classmethod
    def boot(cls, title: str = "") -> "Behavior":
        root = cls(title=title)
        root._cores_available = {
            "ux_dom": importlib.util.find_spec("ux_dom") is not None,
            "ux_channel": importlib.util.find_spec("ux_channel") is not None,
        }
        return root

    def set_plane_backend(
        self,
        plane: str,
        backend: PlaneBackend,
        *,
        host_locked: bool = True,
    ) -> "Behavior":
        """Replace session/client/store backend.

        Host calls (default) lock the plane so attach will not overwrite.
        Wire auto-install uses host_locked=False.
        """
        if plane not in {"session", "client", "store"}:
            raise ValueError(f"unknown plane {plane!r}; use session|client|store")
        self._plane_overrides[plane] = backend
        if host_locked:
            self._plane_host_locked.add(plane)
        return self

    def _backend(self, plane: str) -> PlaneBackend | None:
        if plane in self._plane_overrides:
            return self._plane_overrides[plane]
        return self.planes.backend(plane)

    def plane_get(self, plane: str, inst: Any, fld: Field) -> Any:
        backend = self._backend(plane)
        if backend is None:
            return MISSING
        key = plane_storage_key(plane, inst, fld)
        data = getattr(backend, "data", None)
        if isinstance(data, dict):
            if key not in data:
                return MISSING
            return data[key]
        # Channel / custom backends: get may return MISSING
        val = backend.get(key, fld.default)
        if val is MISSING:
            return MISSING
        # If backend has no has() and returns default for missing keys,
        # prefer instance mirror when never written — ChannelSession always has get
        return val

    def plane_set(self, plane: str, inst: Any, fld: Field, value: Any) -> None:
        backend = self._backend(plane)
        if backend is None:
            return
        key = plane_storage_key(plane, inst, fld)
        backend.set(key, value)

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
        self._region_render = render
        if uid:
            self._region_uid = uid
        return self

    def attach(self, asgi: Any, **kwargs: Any) -> Any:
        from ux_behavior.wire.attach import attach as attach_wire

        return attach_wire(self, asgi, **kwargs)

    def control(self, action: Any, **args: Any) -> dict[str, str]:
        from ux_behavior.wire.control import control_attrs

        return control_attrs(self, action, **args)

    def submit(self, action: str, args: dict[str, Any] | None = None, **kwargs: Any) -> list[Op]:
        payload = dict(args or {})
        payload.update(kwargs)
        return self.dispatch(action, **payload)

    def add(self, component: Type[Any] | Any) -> Any:
        if isinstance(component, type):
            inst = component()
        else:
            inst = component
        cid = getattr(inst, "id", None) or getattr(component, "__name__", "component")
        cid = str(cid)
        if not cid:
            raise ValueError("component id must be a non-empty string")
        bind = getattr(inst, "bind_behavior", None)
        if callable(bind):
            bind(self)
        else:
            setattr(inst, "_behavior", self)
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
