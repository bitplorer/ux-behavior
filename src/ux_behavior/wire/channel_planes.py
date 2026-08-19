"""Channel-backed plane adapters — failures reported, never silent."""

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
    def __init__(self, channel_state: Any, *, diagnostics: Any = None) -> None:
        self._st = channel_state
        self._mirror: dict[str, Any] = {}
        self._diag = diagnostics

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._mirror:
            return self._mirror[key]
        return MISSING

    def set(self, key: str, value: Any) -> None:
        self._mirror[key] = value
        try:
            self._st.client.set(key, value)
        except Exception as exc:
            if self._diag is not None:
                self._diag.warn(
                    "CLIENT_PLANE_PUSH_FAILED",
                    f"client.set failed for {key!r}: {exc}",
                    key=key,
                    error=type(exc).__name__,
                )
            else:
                raise


def try_install_channel_planes(behavior: Any, channel: Any) -> dict[str, str]:
    state = behavior.state
    diag = getattr(behavior, "diagnostics", None)
    report: dict[str, str] = dict(state.report)

    try:
        from ux_channel import state as channel_state_fn
    except ImportError as exc:
        if diag is not None:
            diag.warn("PLANES_NO_CHANNEL_STATE", str(exc))
        return report

    try:
        st = channel_state_fn(channel, allow=("ui.theme", "ui.density"))
    except Exception as exc:
        if diag is not None:
            diag.warn(
                "PLANES_STATE_FAILED",
                f"channel state() failed: {exc}",
                error=type(exc).__name__,
            )
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
        except Exception as exc:
            report["session"] = "memory"
            if diag is not None:
                diag.warn(
                    "PLANE_SESSION_FALLBACK",
                    f"session stayed memory: {exc}",
                    error=type(exc).__name__,
                )

    if not state.is_locked("client"):
        try:
            state.use(
                "client",
                ChannelClientBackend(st, diagnostics=diag),
                lock=False,
                source="channel",
            )
            report["client"] = "channel"
        except Exception as exc:
            report["client"] = "memory"
            if diag is not None:
                diag.warn(
                    "PLANE_CLIENT_FALLBACK",
                    f"client stayed memory: {exc}",
                    error=type(exc).__name__,
                )

    report.setdefault("store", state.report.get("store", "memory"))
    behavior._channel_state = st
    return report
