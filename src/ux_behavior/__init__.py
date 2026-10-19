"""ux-behavior — standard Channel interface for product behavior.

Public surface is intentionally small. Prefer::

    from ux_behavior import Behavior, Component, ComponentProtocol, MorphState, RefState, action, bind

Async entry points live on ``Behavior``: ``async_dispatch``, ``async_submit``,
``async_emit``. Continuations: ``follow_up`` + ``Behavior.emit``.
"""

from ux_behavior._version import __version__
from ux_behavior.action import action, bind
from ux_behavior.chrome import close, confirm, open, select
from ux_behavior.component import Component, ComponentProtocol
from ux_behavior.errors import (
    AuthorityError,
    BehaviorError,
    ContinuationError,
    ValidationError,
)
from ux_behavior.events import Continuation, follow_up
from ux_behavior.fields import KeepState, MorphState, PrefState, RefState, UiState
from ux_behavior.ops import Op, go, notify, submit_outcome, update
from ux_behavior.planes import DictBackend
from ux_behavior.root import Behavior
from ux_behavior.state_api import StateAPI

__all__ = [
    "AuthorityError",
    "Behavior",
    "BehaviorError",
    "Component",
    "ComponentProtocol",
    "Continuation",
    "ContinuationError",
    "DictBackend",
    "KeepState",
    "MorphState",
    "Op",
    "PrefState",
    "RefState",
    "StateAPI",
    "UiState",
    "ValidationError",
    "__version__",
    "action",
    "bind",
    "close",
    "confirm",
    "follow_up",
    "go",
    "notify",
    "open",
    "select",
    "submit_outcome",
    "update",
]
