# Wire door (Channel integration)

## 1. Role

`ux_behavior.wire` is the **only** subtree allowed to import `ux_channel`. All live behavior enters through:

```python
app.attach(asgi, *, secret=None, path="/ux-channel", region=None, uid=None, channel_planes=True)
```

## 2. attach sequence

```text
1. Idempotent if _wire already set
2. asgi is None → warn, return None
3. Import Channel → else CHANNEL_MISSING, return None
4. Resolve secret (env or dev default + warn)
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
- Always `_trusted=True` after Channel acceptance.

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
| ATTACH_DEV_SECRET | warn | Set production secret |
| PLANES_*_FALLBACK | warn | Inspect Channel state API |
| DRIVERS_FAILED | warn | Register drivers on Host |
