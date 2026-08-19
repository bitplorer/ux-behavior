# Component field state

## Canonical pair

| API | Effect | Industry |
|-----|--------|----------|
| **`MorphState`** | may auto-morph on change + `return None` | `useState` |
| **`RefState`** | never auto-morph | `useRef` |

```python
MorphState("home")
MorphState(1, backend="store")
MorphState("system", backend="client", key="ui.theme")
MorphState(0, type=int)               # exact type, no coerce
MorphState("", validate=check_email)  # callable
RefState(None)
```

## Write guards

| Param | Role |
|-------|------|
| **`type=`** | Exact Python type; no coerce (ux-app Sealed intent) |
| **`validate=`** | Callable ``(value) -> value``; may raise |

Do **not** use ``seal=`` on fields — Cap sealing is Channel language.

## backend=

`session` | `client` | `store` | PlaneBackend

Sugar: `UiState`, `PrefState`, `KeepState`.
Aliases: Session/Client/Store/Transient.
