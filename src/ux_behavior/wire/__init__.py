"""Progressive wire door.

Only this package may speak Channel *wire shape* or soft-attach live cores.
Authors stay on the top-level surface; Hosts that need a live Result import here.
"""

from ux_behavior.wire.compose import Conflict, as_selector, compose, lower
from ux_behavior.wire.result import Result
from ux_behavior.wire.attach import attach, attach_info, present, probe

__all__ = [
    "Conflict",
    "Result",
    "as_selector",
    "compose",
    "lower",
    "attach",
    "attach_info",
    "present",
    "probe",
]
