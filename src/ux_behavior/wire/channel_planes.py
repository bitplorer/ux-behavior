"""Channel-backed plane adapters (wire door only).

Installed automatically on successful attach unless Host locked the plane.
Fail-closed: any import/API error leaves MemoryPlanes in place.
"""

from __future__ import annotations

from typing import Any

from ux_behavior.planes import MISSING, PlaneBackend


class ChannelSessionBackend:
    """st.session(key, default).get/set"""

    def __init__(self, channel_state: Any) -> None:
        self._st = channel_state

    def get(self, key: str, default: Any = None) -> Any:
        var = self._st.session(key, default)
        return var.get(default)

    def set(self, key: str, value: Any) -> None:
        self._st.session(key).set(value)


class ChannelClientBackend:
    """Writes enqueue browser client ops; reads use local mirror (MISSING)."""

    def __init__(self, channel_state: Any) -> None:
        self._st = channel_state
        self._mirror: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._mirror:
            return self._mirror[key]
        return MISSING  # Field falls back to instance default/mirror

    def set(self, key: str, value: Any) -> None:
        self._mirror[key] = value
        try:
            self._st.client.set(key, value)
        except Exception:
            # fail-closed: keep mirror; do not raise into product action
            pass


def try_install_channel_planes(behavior: Any, channel: Any) -> dict[str, str]:
    """Install sensible Channel defaults for unlocked planes.

    Returns map of plane → "channel" | "skipped_host" | "skipped_error".
    """
    report: dict[str, str] = {}
    locked = getattr(behavior, "_plane_host_locked", set()) or set()

    try:
        from ux_channel import state as channel_state_fn
    except ImportError:
        return {"session": "skipped_error", "client": "skipped_error"}

    try:
        allow = tuple(
            getattr(getattr(behavior, "runtime", None), "client_state", ()) or ()
        )
        st = channel_state_fn(channel, allow=allow or ("ui.theme", "ui.density"))
    except Exception:
        return {"session": "skipped_error", "client": "skipped_error"}

    if "session" not in locked:
        try:
            behavior.set_plane_backend(
                "session", ChannelSessionBackend(st), host_locked=False
            )
            report["session"] = "channel"
        except Exception:
            report["session"] = "skipped_error"
    else:
        report["session"] = "skipped_host"

    if "client" not in locked:
        try:
            behavior.set_plane_backend(
                "client", ChannelClientBackend(st), host_locked=False
            )
            report["client"] = "channel"
        except Exception:
            report["client"] = "skipped_error"
    else:
        report["client"] = "skipped_host"

    # store stays memory unless Host plugs kv — no silent Channel invent
    report.setdefault("store", "memory")
    behavior._channel_state = st
    behavior._plane_channel_report = report
    return report
