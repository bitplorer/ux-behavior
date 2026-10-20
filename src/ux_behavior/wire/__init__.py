"""Progressive wire door.

Only this package may speak Channel *wire shape* or soft-attach live cores.
Authors stay on the top-level surface; Hosts that need a live Result import here.
"""

from ux_behavior.wire.attach import (
    DEBUG_TRUTHY,
    attach,
    attach_info,
    attach_secret_problem,
    debug_requests_dev,
    present,
    probe,
)
from ux_behavior.wire.compose import Conflict, as_selector, compose, lower
from ux_behavior.wire.events import client_event
from ux_behavior.wire.result import Result

__all__ = [
    "Conflict",
    "DEBUG_TRUTHY",
    "Result",
    "as_selector",
    "attach",
    "attach_info",
    "attach_secret_problem",
    "client_event",
    "compose",
    "debug_requests_dev",
    "lower",
    "present",
    "probe",
]
