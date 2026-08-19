"""ux-behavior — product behavior becomes verified Ops.

Standard Channel interface for Host product behavior:
Component + @action + MorphState/RefState, Behavior root, wire door.
"""

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
from ux_behavior.errors import BehaviorError, AuthorityError, ContinuationError

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
    "Op",
    "__version__",
]
