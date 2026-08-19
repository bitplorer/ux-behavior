"""ux-behavior — standard Channel interface for product behavior."""

from ux_behavior._version import __version__
from ux_behavior.root import Behavior
from ux_behavior.component import Component
from ux_behavior.action import action
from ux_behavior.ops import Op, update, notify, go, submit_outcome
from ux_behavior.chrome import open, close, select, confirm
from ux_behavior.fields import MorphState, RefState, UiState, PrefState, KeepState
from ux_behavior.planes import DictBackend
from ux_behavior.state_api import StateAPI
from ux_behavior.events import follow_up, Continuation
from ux_behavior.errors import (
    BehaviorError,
    AuthorityError,
    ContinuationError,
    ValidationError,
)

__all__ = [
    "Behavior",
    "Component",
    "action",
    "update",
    "notify",
    "go",
    "submit_outcome",
    "open",
    "close",
    "select",
    "confirm",
    "MorphState",
    "RefState",
    "UiState",
    "PrefState",
    "KeepState",
    "DictBackend",
    "StateAPI",
    "follow_up",
    "Continuation",
    "BehaviorError",
    "AuthorityError",
    "ContinuationError",
    "ValidationError",
    "Op",
    "__version__",
]
