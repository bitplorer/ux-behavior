"""Channel-backed plane adapters (wire door only)."""

from __future__ import annotations

from typing import Any

from ux_behavior.planes import MISSING


class ChannelSessionBackend:
    def __init__(self, channel_state: Any) -> None:
        self._st = channel_state

    def get(self, key: str, default: Any = None) -> Any:
        return self._st.session(key, default).get(default)

    def set(self, key: str, value: Any) -> None:
        self._st.session(key).set(value)


class ChannelClientBackend:
    def __init__(self, channel_state: Any) -> None:
        self._st = channel_state
        self._mirror: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._mirror:
            return self._mirror[key]
        return MISSING

    def set(self, key: str, value: Any) -> None:
        self._mirror[key] = value
        try:
            self._st.client.set(key, value)
        except Exception:
            pass


def try_install_channel_planes(behavior: Any, channel: Any) -> dict[str, str]:
    """Install Channel backends on unlocked planes via app.state.use(..., lock=False)."""
    state = behavior.state
    report: dict[str, str] = dict(state.report)

    try:
        from ux_channel import state as channel_state_fn
    except ImportError:
        return report

    try:
        st = channel_state_fn(channel, allow=("ui.theme", "ui.density"))
    except Exception:
        return report

    if not state.is_locked("session"):
        try:
            state.use(
                "session",
                ChannelSessionBackend(st),
                lock=False,
                source="channel",
            )
            report["session"] = "channel"
        except Exception:
            report["session"] = "memory"

    if not state.is_locked("client"):
        try:
            state.use(
                "client",
                ChannelClientBackend(st),
                lock=False,
                source="channel",
            )
            report["client"] = "channel"
        except Exception:
            report["client"] = "memory"

    report.setdefault("store", state.report.get("store", "memory"))
    behavior._channel_state = st
    return report
