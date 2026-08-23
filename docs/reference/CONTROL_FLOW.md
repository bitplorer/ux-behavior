# Control flow, Caps, diagnostics

> **Diátaxis:** reference · **Canonical:** `docs/reference/CONTROL_FLOW.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## Happy paths

### Offline test / SSR

```text
boot → add → dispatch(public action) → list[Op]
```

### Live

```text
boot → add → region → attach(asgi)
  → Channel boot
  → optional channel planes + drivers
button: control(action) → Cap attrs (if mint OK)
inbound: Channel auth → async_dispatch(..., _trusted=True)
```

## Caps matrix

| Action caps | Offline | Attached wire |
|-------------|---------|---------------|
| `()` | runs | runs |
| non-empty | **AuthorityError** unless trust/`_trusted` | runs (Channel already gated) |

## Validation

Bad / mistyped kwargs → **does not raise to Host** by default.
Returns morph Ops targeting `{action}.{field}-error`.
Diagnostics: `VALIDATION_FAILED` + hint.

## Attach outcomes

| Case | Result | Diagnostic |
|------|--------|------------|
| `asgi is None` | `None` | ATTACH_NO_ASGI |
| no ux_channel | `None` | CHANNEL_MISSING |
| boot error | `None` or raise if `strict_attach` | ATTACH_BOOT_FAILED |
| success | Channel | ATTACH_OK |

## Control outcomes

| Case | Result |
|------|--------|
| no wire | offline attrs + CONTROL_OFFLINE |
| mint OK | Channel attrs + CONTROL_MINTED |
| mint fail | offline attrs + CONTROL_MINT_FAILED; raise if `strict_control` |

## Diagnostics API

```python
app.diagnostics.events       # DiagEvent list
app.diagnostics.summary()    # counts, codes, events with hint
app.diagnostics.last_hint()
app.diagnostics.has_errors()
app.diagnostics.clear()
```

Each event: `level`, `code`, `message`, **`hint`** (next step), `context`, `at`.

## Common codes → next step (summary)

| Code | Next step |
|------|-----------|
| CAP_REQUIRED | Attach Channel or trust() / `_trusted` in tests |
| CHANNEL_MISSING | Install ux-channel; retry attach |
| CONTROL_OFFLINE | Attach for Caps or accept offline SSR |
| VALIDATION_FAILED | Fix args or render error morph targets |
| STAMP_REJECT | `app.use` / `app.domain` |
| CONTINUATION_MISSING | `follow_up` before `emit` |
| ATTACH_DEV_SECRET | Set UX_CHANNEL_SECRET |

Full map: `ux_behavior.diagnostics.HINTS`.
