"""Progressive wire door.

Only this package may speak Channel *wire shape*.
Authors stay on the top-level surface; Hosts that need a live Result import here.
"""

from ux_behavior.wire.compose import Conflict, as_selector, compose, lower
from ux_behavior.wire.result import Result

__all__ = ["Conflict", "Result", "as_selector", "compose", "lower"]
