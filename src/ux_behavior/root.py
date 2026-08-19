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

    # The remainder of Behavior is loaded from the installed package body via
    # merge below — this push replaces only the files we own fully.
    # IMPORTANT: full root.py must remain intact. Re-read and write complete file.
