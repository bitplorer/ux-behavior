"""Composition root — standard Channel interface for product behavior."""

from __future__ import annotations

import importlib.util
from typing import Any, Callable, Iterable, Type

from ux_behavior.domains import DomainTable, default_table
from ux_behavior.errors import AuthorityError, ContinuationError
from ux_behavior.events import Continuation, _begin_follow_ups, _end_follow_ups
from ux_behavior.fields import Field, plane_storage_key, ref_field_names
from ux_behavior.ops import Op, update
from ux_behavior.planes import MISSING
from ux_behavior.state_api import StateAPI


def _public_state(inst: Any) -> dict[str, Any]:
    skip = ref_field_names(inst)
    out: dict[str, Any] = {}
    for key, value in vars(inst).items():
        if key.startswith("_"):
            continue
        if key in skip:
            continue
        out[key] = value
    return out


class Behavior:
    """Composition root for product behavior.

    Hosts: boot → add components → optional state.use / attach → dispatch.
    """

    def __init__(
        self,
        title: str = "",
        domains: DomainTable | None = None,
        *,
        strict_caps: bool = True,
    ) -> None:
        self.title = title
        self.strict_caps = strict_caps
        self._components: dict[str, Any] = {}
        self.domains = domains or default_table()
        self.state = StateAPI(self)
        self._continuations: dict[str, Continuation] = {}
        self._cores_available: dict[str, bool] = {
            "ux_dom": False,
            "ux_channel": False,
        }
        self._wire: Any = None
        self._region_render: Callable[[], Any] | None = None
        self._region_uid: str | None = None

    @classmethod
    def boot(
        cls,
        title: str = "",
        *,
        strict_caps: bool = True,
    ) -> "Behavior":
        root = cls(title=title, strict_caps=strict_caps)
        root._cores_available = {
            "ux_dom": importlib.util.find_spec("ux_dom") is not None,
            "ux_channel": importlib.util.find_spec("ux_channel") is not None,
        }
        return root

    def _backend_for(self, plane: str, fld: Field | None = None) -> Any:
        if fld is not None and getattr(fld, "custom_backend", None) is not None:
            return fld.custom_backend
        return self.state.backend(plane)

    def plane_get(self, plane: str, inst: Any, fld: Field) -> Any:
        backend = self._backend_for(plane, fld)
        if backend is None:
            return MISSING
        key = plane_storage_key(plane, inst, fld)
        data = getattr(backend, "data", None)
        if isinstance(data, dict):
            if key not in data:
                return MISSING
            return data[key]
        val = backend.get(key, fld.default)
        if val is MISSING:
            return MISSING
        return val

    def plane_set(self, plane: str, inst: Any, fld: Field, value: Any) -> None:
        backend = self._backend_for(plane, fld)
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

    @property
    def continuations(self) -> dict[str, Continuation]:
        return dict(self._continuations)

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

    def submit(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Op]:
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

    def _require_caps(self, fn: Any, action: str, *,
                      trusted: bool) -> None:
        caps = tuple(getattr(fn, "_ux_behavior_caps", ()) or ())
        if not caps:
            return
        if trusted:
            return
        # Live Channel path verifies Cap before invoking dispatch from wire.
        if self._wire is not None:
            return
        if self.strict_caps:
            raise AuthorityError(
                f"{action!r} requires Cap {caps}; "
                "attach Channel, use control() under wire, or dispatch(..., _trusted=True) in tests"
            )

    def dispatch(self, action: str, **kwargs: Any) -> list[Op]:
        if "." not in action:
            raise ValueError(
                f"action name must be 'component.method', got {action!r}"
            )
        trusted = bool(kwargs.pop("_trusted", False))
        component_id, method = action.rsplit(".", 1)
        inst = self.get(component_id)
        fn = getattr(inst, method, None)
        if fn is None or not callable(fn):
            raise AttributeError(f"unknown action {action!r}")
        if not getattr(fn, "_ux_behavior_action", False):
            raise TypeError(f"{action!r} is not marked with @action")

        self._require_caps(fn, action, trusted=trusted)

        token = _begin_follow_ups()
        before = _public_state(inst)
        try:
            result = fn(**kwargs)
        finally:
            pending = _end_follow_ups(token)

        for item in pending:
            self._continuations[item.event] = item

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

    def emit(self, event: str, **slots: Any) -> list[Op]:
        """Fire a continuation registered by follow_up during a prior action."""
        event = str(event or "").strip()
        item = self._continuations.get(event)
        if item is None:
            raise ContinuationError(f"no continuation for event {event!r}")
        resolved = dict(item.args)
        for dest, src in item.args_from.items():
            if src in slots:
                resolved[dest] = slots[src]
        for key, value in slots.items():
            if key not in resolved:
                resolved[key] = value
        # Continuation runs with trust: Cap was established when follow_up was recorded
        # under an authorized action. Live Hosts should still gate emit at the edge.
        return self.dispatch(item.action, _trusted=True, **resolved)

    def _check_stamp(self, ops: list[Op]) -> None:
        for op in ops:
            if not isinstance(op, Op):
                raise TypeError(f"expected Op, got {type(op).__name__}")
            if not self.domains.allows(*op.pair):
                raise PermissionError(
                    f"pair {op.fq} is not on the session stamp"
                )
