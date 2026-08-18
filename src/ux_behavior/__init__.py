"""ux-behavior — product behavior becomes verified Ops.

Cold import stays clean. Cores are never imported from application code.
"""

from ux_behavior._version import __version__
from ux_behavior.root import Behavior
from ux_behavior.component import Component
from ux_behavior.action import action
from ux_behavior.ops import Op, update, notify, go, form_result
from ux_behavior.chrome import open, close, select, confirm

__all__ = [
    "Behavior",
    "Component",
    "action",
    "update",
    "notify",
    "go",
    "form_result",
    "open",
    "close",
    "select",
    "confirm",
    "Op",
    "__version__",
]
