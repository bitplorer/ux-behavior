# Wire door (Channel integration)

> **Diátaxis:** reference · **Canonical:** `docs/reference/WIRE.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## 1. Role

`ux_behavior.wire` is the **only** subtree allowed to import `ux_channel`. All live behavior enters through:

```python
app.attach(asgi, *, secret=None, path="/ux-channel", region=None, uid=None, channel_planes=True)
```

## 2. attach sequence

```text
1. Idempotent if _wire already set
2. asgi is None → warn, return None
3. Import Channel → else CHANNEL_MISSING, return None (raise if strict_attach).
   A host without ux-channel gets None even when no secret is configured.
4. Resolve secret. Outside dev, a missing secret or the public dev constant
   raises (ATTACH_SECRET_REQUIRED). Dev is DEBUG in 1/true/yes/on after
   strip + lower (this package has no other dev switch). The switch is
   public: `from ux_behavior.wire import DEBUG_TRUTHY, debug_requests_dev`;
   `debug_requests_dev(env=None)` reads `env` or `os.environ`. In dev, a missing
   secret is one random per-process value, same shape as
   ChannelConfig.development() (ATTACH_DEV_SECRET warn). The public
   constant is never accepted, including ChannelConfig.production when
   REDIS_URL is set. `REDIS_URL` with no configured secret raises even
   when `DEBUG=1`, because that store is shared by more than one process.
   Set `UX_CHANNEL_SECRET` even in dev when using `--workers` greater
   than 1, `--reload`, or `REDIS_URL`. A per-process secret does not
   survive a restart, and Caps minted with it fail on the next process.
   The secret then goes through the ChannelConfig this step boots with
   and through ux-channel's `CapService`; a secret they refuse raises
   ATTACH_SECRET_REQUIRED with ux-channel's own message. The length rules
   live in ux-channel only.
   Preflight: `from ux_behavior.wire import attach_secret_problem`;
   `attach_secret_problem(env=None, *, secret=None)` returns None when this
   step accepts, else the exact message it raises. `env` is any
   `Mapping[str, str]` and defaults to `os.environ`. attach() calls the same
   check, so the two cannot disagree. Without ux-channel it returns a
   message, because the secret cannot be checked.
5. Channel.boot → on failure: error; raise if strict_attach
6. Register region paint callable
7. Register ux_behavior.dispatch handler (prefer async)
8. try_install_channel_planes (unlocked only)
9. try_register_drivers for agreed domain names
10. Set _wire, diagnostic ATTACH_OK
```

## 3. Inbound dispatch handler

- Reads `ux_action` + args/form.
- Empty action → warn, no-op.
- On exception: `DISPATCH_FAILED` + **re-raise** (not swallowed).
- Always the private trust sentinel after Channel acceptance. A payload `_trusted` value is dropped.

## 4. control path

See SECURITY.md. Implementation: `wire.control.control_attrs`.

## 5. Plane adapters

| Adapter | Maps to |
|---------|--------|
| ChannelSessionBackend | `st.session(key)` |
| ChannelClientBackend | local mirror + `st.client.set`; push failures **warn**, mirror kept |

## 6. Drivers

If Host called `app.use("effects"|"search")`, attach attempts `channel.use(name)` when available. Outcomes recorded (`channel` vs `skipped`). Stamp agreement does not require drivers to exist; apply still needs Channel/Host wiring for real notice/search side effects.

## 7. Failure matrix (attach)

| Code | Severity | Host action |
|------|----------|-------------|
| CHANNEL_MISSING | error | Install channel package |
| ATTACH_BOOT_FAILED | error | Fix config/secret/Redis |
| ATTACH_SECRET_REQUIRED | error | Set UX_CHANNEL_SECRET; the public dev secret and secrets ux-channel refuses are refused. Check first with `attach_secret_problem()` |
| ATTACH_DEV_SECRET | warn | DEBUG boot is using a per-process secret |
| PLANES_*_FALLBACK | warn | Inspect Channel state API |
| DRIVERS_FAILED | warn | Register drivers on Host |

## 8. CustomEvent (`client_event`)

Host-only. Not a Behavior `Op`. Not on the frozen public surface.

```python
from ux_behavior.wire import client_event
from ux_channel.protocol.types import Result

@ch.on("cart.add")
async def cart_add(ctx, sku: str):
    with app.trust():
        await app.async_dispatch("cart.add", sku=sku)
    return Result.success(
        client_event("cart:added", target="#cart", detail={"sku": sku}),
    )
```

`with app.trust()` lends trust to a task created inside the block, and that
task keeps it for its whole life. See the
[spawned-task warning](SECURITY.md#trust-context). A second wire that has
already verified the Cap can call `await app.async_dispatch_verified(name, payload)`
instead. That grant is one call and does not spread to spawned tasks.

Wire shape: `{op: "dispatch", name, target?, detail?, bubbles?}`.
`target` is a CSS selector; omit → classic `ux-channel.js` fires on `document.body`.
Components still return `list[Op] | None`. Stock `attach()` still `return None`.
This helper is for the Host `@ch.on` that returns a Channel Result.
