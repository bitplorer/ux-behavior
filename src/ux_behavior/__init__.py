"""ux-behavior — product behavior becomes verified Ops.

Cold import stays clean. Cores are never imported from application code.
"""

from ux_behavior._version import __version__
from ux_behavior.root import Behavior
from ux_behavior.component import Component
from ux_behavior.action import action
from ux_behavior.ops import Op, update, notify, go, submit_outcome
from ux_behavior.chrome import open, close, select, confirm
from ux_behavior.fields import (
    SessionState,
    ClientState,
    StoreState,
    TransientState,
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
    "SessionState",
    "ClientState",
    "StoreState",
    "TransientState",
    "Op",
    "__version__",
]
