"""Progressive wire door.

Only this package may speak Channel *wire shape* or soft-attach live cores.
Authors stay on the top-level surface; Hosts that need a live Result import here.
"""

from ux_behavior.wire.attach import attach, attach_info, present, probe
from ux_behavior.wire.compose import Conflict, as_selector, compose, lower
from ux_behavior.wire.events import client_event
from ux_behavior.wire.result import Result

__all__ = [
    "Conflict",
    "Result",
    "as_selector",
    "attach",
    "attach_info",
    "client_event",
    "compose",
    "lower",
    "present",
    "probe",
]
