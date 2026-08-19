"""Composition root — standard Channel interface for product behavior.

Sync and async are first-class. Failures are explicit (raise or diagnostics).
Production default: ``developer_hints=False`` so Cap errors never include
bypass recipes (trust / _trusted) in exception text or diagnostics.
"""

from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from typing import Any, Callable, Iterable, Iterator, Type

from ux_behavior.client_risk import check_client_write
from ux_behavior.diagnostics import Diagnostics
from ux_behavior.domains import DomainTable, default_table
from ux_behavior.errors import AuthorityError, ContinuationError, ValidationError
from ux_behavior.events import Continuation, _begin_follow_ups, _end_follow_ups
from ux_behavior.fields import Field, plane_storage_key, ref_field_names
from ux_behavior.ops import Op, update
from ux_behavior.planes import MISSING
from ux_behavior.state_api import StateAPI
from ux_behavior.validate import bind_action_args


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
    """Composition root. Dumb Hosts: boot → add → attach → control / dispatch."""

    def __init__(
        self,
        title: str = "",
        domains: DomainTable | None = None,
        *,
        strict_caps: bool = True,
        client_risk: bool = True,
        strict_control: bool = False,
        strict_attach: bool = False,
        developer_hints: bool = False,
    ) -> None:
        self.title = title
        self.strict_caps = strict_caps
        self.client_risk = client_risk
        self.strict_control = strict_control
        self.strict_attach = strict_attach
        self.developer_hints = developer_hints
        self.diagnostics = Diagnostics(developer_hints=developer_hints)
        self._components: dict[str, Any] = {}
        self.domains = domains or default_table()
        self.state = StateAPI(self)
        self._continuations: dict[str, Continuation] = {}
        self._preview = False
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
        client_risk: bool = True,
        strict_control: bool = False,
        strict_attach: bool = False,
        developer_hints: bool = False,
    ) -> "Behavior":
        root = cls(
            title=title,
            strict_caps=strict_caps,
            client_risk=client_risk,
            strict_control=strict_control,
            strict_attach=strict_attach,
            developer_hints=developer_hints,
        )
        root._cores_available = {
            "ux_dom": importlib.util.find_spec("ux_dom") is not None,
            "ux_channel": importlib.util.find_spec("ux_channel") is not None,
        }
        if not root._cores_available["ux_channel"]:
            root.diagnostics.info(
                "CORE_CHANNEL_ABSENT",
                "ux_channel not installed; live Caps unavailable until install+attach",
            )
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
        if self._preview and plane in {"session", "store"}:
            raise AuthorityError(
                f"preview cannot write {plane} field {fld.name!r}"
            )
        key = plane_storage_key(plane, inst, fld)
        if plane == "client" and self.client_risk:
            check_client_write(key, value)
        backend = self._backend_for(plane, fld)
        if backend is None:
            self.diagnostics.error(
                "PLANE_NO_BACKEND",
                f"no backend for plane {plane!r}",
                plane=plane,
                field=fld.name,
            )
            raise AuthorityError(f"no backend for plane {plane!r}")
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

    @property
    def is_preview(self) -> bool:
        return self._preview

    @contextmanager
    def preview(self) -> Iterator["Behavior"]:
        prev = self._preview
        self._preview = True
        self.diagnostics.info("PREVIEW_ON", "preview mode enabled")
        try:
            yield self
        finally:
            self._preview = prev
            self.diagnostics.info("PREVIEW_OFF", "preview mode disabled")

    @contextmanager
    def trust(self) -> Iterator["Behavior"]:
        prev = self.strict_caps
        self.strict_caps = False
        self.diagnostics.warn("TRUST_ON", "strict_caps disabled in trust() context")
        try:
            yield self
        finally:
            self.strict_caps = prev
            self.diagnostics.info("TRUST_OFF", "strict_caps restored")

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

    def add(self, component: Type[Any] | Any) -> Any:
        if isinstance(component, type):
            inst = component()
        else:
            inst = component
        cid = getattr(inst, "id", None) or getattr(component, "__name__", "component")
        cid = str(cid)
        if not cid:
            raise ValueError("component id must be a non-empty string")
        if cid in self._components:
            self.diagnostics.warn(
                "COMPONENT_REPLACE",
                f"replacing existing component id {cid!r}",
                id=cid,
            )
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

    def _require_caps(self, fn: Any, action: str, *, trusted: bool) -> None:
        caps = tuple(getattr(fn, "_ux_behavior_caps", ()) or ())
        if not caps or trusted or self._wire is not None:
            return
        if self.strict_caps:
            self.diagnostics.error(
                "CAP_REQUIRED",
                f"{action} requires Cap {caps}",
                action=action,
                caps=list(caps),
            )
            raise AuthorityError(
                f"{action!r} requires Cap {caps}",
                hint=(
                    "attach Channel, use app.trust(), or dispatch(..., _trusted=True)"
                    if self.developer_hints
                    else ""
                ),
            )

    def _validation_ops(self, action: str, err: ValidationError) -> list[Op]:
        self.diagnostics.warn(
            "VALIDATION_FAILED",
            str(err),
            action=action,
            fields=dict(err.fields),
        )
        ops: list[Op] = []
        for field, msg in err.fields.items():
            target = f"{action}.{field}-error" if field != "_" else f"{action}-error"
            ops.append(update(target, str(msg)))
        return ops

    def _finish(
        self,
        action: str,
        component_id: str,
        inst: Any,
        before: dict[str, Any],
        result: Any,
        pending: list[Continuation],
    ) -> list[Op]:
        for item in pending:
            self._continuations[item.event] = item
            self.diagnostics.info(
                "CONTINUATION_ARMED",
                f"follow_up {item.event!r} → {item.action}",
                event=item.event,
                action=item.action,
            )

        if result is None:
            after = _public_state(inst)
            ops = self.refresh(component_id) if after != before else []
        elif isinstance(result, list):
            ops = result
        else:
            raise TypeError(
                f"{action!r} returned {type(result).__name__}; expected list[Op] | None"
            )
        self._check_stamp(ops)
        return ops

    def _resolve(self, action: str) -> tuple[str, Any, Any]:
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
        return component_id, inst, fn

    def _continuation_args(
        self, event: str, slots: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        event = str(event or "").strip()
        item = self._continuations.get(event)
        if item is None:
            self.diagnostics.error(
                "CONTINUATION_MISSING",
                f"no continuation for event {event!r}",
                event=event,
            )
            raise ContinuationError(f"no continuation for event {event!r}")
        resolved = dict(item.args)
        for dest, src in item.args_from.items():
            if src in slots:
                resolved[dest] = slots[src]
        for key, value in slots.items():
            if key not in resolved:
                resolved[key] = value
        return item.action, resolved

    def dispatch(self, action: str, **kwargs: Any) -> list[Op]:
        trusted = bool(kwargs.pop("_trusted", False))
        component_id, inst, fn = self._resolve(action)
        if getattr(fn, "_ux_behavior_async", False):
            raise TypeError(
                f"{action!r} is async; use await app.async_dispatch(...)"
            )
        self._require_caps(fn, action, trusted=trusted)
        try:
            clean = bind_action_args(fn, kwargs)
        except ValidationError as err:
            return self._validation_ops(action, err)

        token = _begin_follow_ups()
        before = _public_state(inst)
        try:
            result = fn(**clean)
        finally:
            pending = _end_follow_ups(token)
        return self._finish(action, component_id, inst, before, result, pending)

    async def async_dispatch(self, action: str, **kwargs: Any) -> list[Op]:
        trusted = bool(kwargs.pop("_trusted", False))
        component_id, inst, fn = self._resolve(action)
        self._require_caps(fn, action, trusted=trusted)
        try:
            clean = bind_action_args(fn, kwargs)
        except ValidationError as err:
            return self._validation_ops(action, err)

        token = _begin_follow_ups()
        before = _public_state(inst)
        try:
            if getattr(fn, "_ux_behavior_async", False):
                result = await fn(**clean)
            else:
                result = fn(**clean)
        finally:
            pending = _end_follow_ups(token)
        return self._finish(action, component_id, inst, before, result, pending)

    def submit(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Op]:
        payload = dict(args or {})
        payload.update(kwargs)
        return self.dispatch(action, **payload)

    async def async_submit(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Op]:
        payload = dict(args or {})
        payload.update(kwargs)
        return await self.async_dispatch(action, **payload)

    def emit(self, event: str, **slots: Any) -> list[Op]:
        action, resolved = self._continuation_args(event, slots)
        return self.dispatch(action, _trusted=True, **resolved)

    async def async_emit(self, event: str, **slots: Any) -> list[Op]:
        action, resolved = self._continuation_args(event, slots)
        return await self.async_dispatch(action, _trusted=True, **resolved)

    def _check_stamp(self, ops: list[Op]) -> None:
        for op in ops:
            if not isinstance(op, Op):
                raise TypeError(f"expected Op, got {type(op).__name__}")
            if not self.domains.allows(*op.pair):
                self.diagnostics.error(
                    "STAMP_REJECT",
                    f"pair {op.fq} not on stamp",
                    pair=op.fq,
                )
                raise PermissionError(
                    f"pair {op.fq} is not on the session stamp"
                )
