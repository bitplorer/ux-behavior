# Errors and diagnostics catalog

## Exception types

| Type | Typical cause | Next step |
|------|---------------|----------|
| `AuthorityError` | Cap, preview, client risk, missing plane | Read `.hint`; attach/trust/exit preview/move field |
| `ContinuationError` | `emit` without `follow_up` | Arm continuation in a prior action |
| `ValidationError` | bind failure (internal) | Host usually sees morphs, not this |
| `PermissionError` | Op not on stamp | `app.use` / `domain` |
| `TypeError` | bad @action return; async on sync API | Fix return or use async_dispatch |
| `KeyError` | unknown component id | `app.add` |
| `AttributeError` | unknown method | define `@action` |
| `ValueError` | malformed action name | use `component.method` |
| `RuntimeError` | `follow_up` outside dispatch | call only inside action |

## Diagnostic codes

Every event has `level`, `code`, `message`, **`hint`**, `context`, `at`.

`hint` and `context` are empty unless `Behavior.boot(developer_hints=True)` (tests / local Hosts only).

Primary codes (non-exhaustive; see `ux_behavior.diagnostics.HINTS`):

`CORE_CHANNEL_ABSENT`, `CHANNEL_MISSING`, `ATTACH_*`, `CONTROL_*`, `CAP_REQUIRED`, `VALIDATION_FAILED`, `STAMP_REJECT`, `CONTINUATION_*`, `DISPATCH_*`, `PLANE_*`, `DRIVER_*`, `TRUST_*`, `PREVIEW_*`, `COMPONENT_REPLACE`

## Host handling pattern

```python
try:
    ops = await app.async_dispatch(name, **payload)
except AuthorityError as e:
    log.warning("%s | %s", e, e.hint or app.diagnostics.last_hint())
    # return 403 or morph
except Exception:
    log.error("dispatch failed %s", app.diagnostics.summary())
    raise
```
