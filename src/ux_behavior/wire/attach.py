"""Live Channel attach (progressive door)."""

from __future__ import annotations

import importlib.util
import os
from typing import Any, Callable

DEFAULT_REGION_UID = "app.root"
UX_ACTION_KEY = "ux_action"


def probe() -> dict[str, bool]:
    return {
        "ux_dom": importlib.util.find_spec("ux_dom") is not None,
        "ux_channel": importlib.util.find_spec("ux_channel") is not None,
    }


def present() -> bool:
    return probe().get("ux_channel", False)


def attach_info(behavior: Any | None = None) -> dict[str, Any]:
    available = probe()
    stamp: list[str] = []
    title = ""
    planes: dict[str, str] = {}
    if behavior is not None:
        title = getattr(behavior, "title", "") or ""
        domains = getattr(behavior, "domains", None)
        if domains is not None:
            stamp = sorted(f"{ns}.{name}" for ns, name in domains.stamp)
        state = getattr(behavior, "state", None)
        if state is not None:
            planes = dict(state.report)
    return {
        "title": title,
        "cores": available,
        "stamp": stamp,
        "ready_for_live": bool(available.get("ux_channel")),
        "attached": getattr(behavior, "_wire", None) is not None,
        "planes": planes,
    }


def attach(
    behavior: Any,
    asgi: Any,
    *,
    secret: str | None = None,
    path: str = "/ux-channel",
    region: Callable[[], Any] | None = None,
    uid: str | None = None,
    channel_planes: bool = True,
) -> Any:
    if region is not None:
        behavior._region_render = region
    if uid:
        behavior._region_uid = uid

    existing = getattr(behavior, "_wire", None)
    if existing is not None:
        return existing
    if asgi is None:
        return None

    try:
        from ux_channel import Channel, ChannelConfig
    except ImportError:
        return None

    secret = (
        secret
        or os.environ.get("UX_CHANNEL_SECRET")
        or os.environ.get("UX_BEHAVIOR_SECRET")
        or "dev-secret-key-32chars-minimum!!!!"
    )
    if os.environ.get("REDIS_URL"):
        cfg = ChannelConfig.production(secret).with_redis(os.environ["REDIS_URL"])
    else:
        cfg = ChannelConfig.development(secret=secret, allow_memory_stores=True)

    ch = Channel.boot(asgi, config=cfg, path=path)
    slot_uid = getattr(behavior, "_region_uid", None) or DEFAULT_REGION_UID

    def _paint(ctx=None):
        fn = getattr(behavior, "_region_render", None)
        if not callable(fn):
            return ""
        tree = fn()
        if tree is None:
            return ""
        if hasattr(tree, "__render__"):
            return tree.__render__(pretty=False)
        return str(tree)

    slot = ch.region(slot_uid)(_paint)

    @ch.on("ux_behavior.dispatch", refresh=[slot], idempotent=False)
    def dispatch(ctx, ux_action: str = "", **args: Any):
        reserved = {UX_ACTION_KEY}
        payload = {k: v for k, v in args.items() if k not in reserved}
        if ctx is not None:
            form = getattr(ctx, "form", None) or getattr(ctx, "data", None) or {}
            if isinstance(form, dict):
                for key, value in form.items():
                    if key in reserved:
                        continue
                    if key not in payload:
                        payload[str(key)] = value
        name = str(ux_action or "")
        if not name:
            return None
        behavior.dispatch(name, **payload)
        return None

    behavior._wire = ch
    behavior._dispatch = dispatch
    behavior._region_uid = slot_uid

    if channel_planes:
        try:
            from ux_behavior.wire.channel_planes import try_install_channel_planes

            try_install_channel_planes(behavior, ch)
        except Exception:
            pass

    return ch
