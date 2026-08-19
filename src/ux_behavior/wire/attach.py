"""Live Channel attach (progressive door) — no silent attach failure."""

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
    diag: dict[str, Any] = {}
    if behavior is not None:
        title = getattr(behavior, "title", "") or ""
        domains = getattr(behavior, "domains", None)
        if domains is not None:
            stamp = sorted(f"{ns}.{name}" for ns, name in domains.stamp)
        state = getattr(behavior, "state", None)
        if state is not None:
            planes = dict(state.report)
        d = getattr(behavior, "diagnostics", None)
        if d is not None:
            diag = d.summary()
    return {
        "title": title,
        "cores": available,
        "stamp": stamp,
        "ready_for_live": bool(available.get("ux_channel")),
        "attached": getattr(behavior, "_wire", None) is not None,
        "planes": planes,
        "diagnostics": diag,
    }


def _payload_from(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
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
    return payload


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
    diag = getattr(behavior, "diagnostics", None)

    if region is not None:
        behavior._region_render = region
    if uid:
        behavior._region_uid = uid

    existing = getattr(behavior, "_wire", None)
    if existing is not None:
        if diag is not None:
            diag.info("ATTACH_IDEMPOTENT", "attach() called again; returning existing wire")
        return existing

    if asgi is None:
        if diag is not None:
            diag.warn("ATTACH_NO_ASGI", "attach(asgi=None) — not live")
        return None

    try:
        from ux_channel import Channel, ChannelConfig
    except ImportError as exc:
        if diag is not None:
            diag.error(
                "CHANNEL_MISSING",
                "ux_channel not installed; attach aborted",
                error=str(exc),
            )
        if getattr(behavior, "strict_attach", False):
            raise
        return None

    secret = (
        secret
        or os.environ.get("UX_CHANNEL_SECRET")
        or os.environ.get("UX_BEHAVIOR_SECRET")
        or ""
    )
    if not secret:
        secret = "dev-secret-key-32chars-minimum!!!!"
        if diag is not None:
            diag.warn(
                "ATTACH_DEV_SECRET",
                "using built-in dev secret; set UX_CHANNEL_SECRET in production",
            )

    try:
        if os.environ.get("REDIS_URL"):
            cfg = ChannelConfig.production(secret).with_redis(os.environ["REDIS_URL"])
        else:
            cfg = ChannelConfig.development(secret=secret, allow_memory_stores=True)
        ch = Channel.boot(asgi, config=cfg, path=path)
    except Exception as exc:
        if diag is not None:
            diag.error(
                "ATTACH_BOOT_FAILED",
                f"Channel.boot failed: {exc}",
                error=type(exc).__name__,
            )
        if getattr(behavior, "strict_attach", False):
            raise
        return None

    slot_uid = getattr(behavior, "_region_uid", None) or DEFAULT_REGION_UID

    def _paint(ctx=None):
        fn = getattr(behavior, "_region_render", None)
        if not callable(fn):
            if diag is not None:
                diag.warn("REGION_EMPTY", "no region render callable; painting empty")
            return ""
        tree = fn()
        if tree is None:
            return ""
        if hasattr(tree, "__render__"):
            return tree.__render__(pretty=False)
        return str(tree)

    slot = ch.region(slot_uid)(_paint)

    async def _run_dispatch(ctx: Any, ux_action: str, args: dict[str, Any]) -> None:
        name = str(ux_action or "")
        if not name:
            if diag is not None:
                diag.warn("DISPATCH_EMPTY_ACTION", "inbound event missing ux_action")
            return
        try:
            await behavior.async_dispatch(
                name, _trusted=True, **_payload_from(ctx, args)
            )
        except Exception as exc:
            if diag is not None:
                diag.error(
                    "DISPATCH_FAILED",
                    f"async_dispatch failed: {exc}",
                    action=name,
                    error=type(exc).__name__,
                )
            raise

    try:

        @ch.on("ux_behavior.dispatch", refresh=[slot], idempotent=False)
        async def dispatch_async(ctx, ux_action: str = "", **args: Any):
            await _run_dispatch(ctx, ux_action, args)
            return None

        behavior._dispatch = dispatch_async
        if diag is not None:
            diag.info("ATTACH_ASYNC_HANDLER", "registered async dispatch handler")
    except Exception as exc:
        if diag is not None:
            diag.warn(
                "ATTACH_ASYNC_HANDLER_FAILED",
                f"async handler rejected ({exc}); falling back to sync",
                error=type(exc).__name__,
            )

        @ch.on("ux_behavior.dispatch", refresh=[slot], idempotent=False)
        def dispatch_sync(ctx, ux_action: str = "", **args: Any):
            name = str(ux_action or "")
            if not name:
                if diag is not None:
                    diag.warn("DISPATCH_EMPTY_ACTION", "inbound event missing ux_action")
                return None
            try:
                behavior.dispatch(name, _trusted=True, **_payload_from(ctx, args))
            except Exception as err:
                if diag is not None:
                    diag.error(
                        "DISPATCH_FAILED",
                        f"dispatch failed: {err}",
                        action=name,
                        error=type(err).__name__,
                    )
                raise
            return None

        behavior._dispatch = dispatch_sync

    behavior._wire = ch
    behavior._region_uid = slot_uid
    if diag is not None:
        diag.info("ATTACH_OK", "Channel attached", path=path, region=slot_uid)

    if channel_planes:
        try:
            from ux_behavior.wire.channel_planes import try_install_channel_planes

            report = try_install_channel_planes(behavior, ch)
            if diag is not None:
                diag.info("PLANES_INSTALLED", "channel plane backends", **report)
        except Exception as exc:
            if diag is not None:
                diag.warn(
                    "PLANES_INSTALL_FAILED",
                    f"channel planes not installed: {exc}",
                    error=type(exc).__name__,
                )

    try:
        from ux_behavior.wire.drivers import try_register_drivers

        dreport = try_register_drivers(behavior, ch)
        if diag is not None and dreport:
            diag.info("DRIVERS_REPORT", "driver registration", **dreport)
    except Exception as exc:
        if diag is not None:
            diag.warn(
                "DRIVERS_FAILED",
                f"driver registration failed: {exc}",
                error=type(exc).__name__,
            )

    return ch
