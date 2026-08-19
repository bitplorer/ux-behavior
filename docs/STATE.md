# Component field state

## Canonical pair

| API | Effect | Industry |
|-----|--------|----------|
| **`MorphState`** | change + `return None` → may auto-morph | `useState` |
| **`RefState`** | change + `return None` → never auto-morph | `useRef` |

```python
from ux_behavior import MorphState, RefState, UiState, PrefState, KeepState

page  = MorphState("home")                                 # session
theme = MorphState("system", backend="client", key="ui.theme")
step  = MorphState(1, backend="store")
n     = MorphState(0, seal=int)
token = RefState(None)

# sugar
page  = UiState("home")
theme = PrefState("system", key="ui.theme")
step  = KeepState(1)
```

## Rules

1. **Morph vs Ref** is the only effect split.
2. **backend=** only on MorphState: `session` | `client` | `store` | PlaneBackend.
3. **seal=** opt-in exact type or callable; no coerce for types.
4. Explicit `return [update(...)]` still morphs even if only RefState changed.
5. Domain data (cart, orders) is Host store/DB — not field state.
6. Toasts use `notify` — not RefState.
7. RefState is not a DOM ref.

## Host backends

```python
app.set_plane_backend("store", kv)
app.attach(asgi)  # Channel session/client defaults unless locked
```

## Aliases

`SessionState`/`ClientState`/`StoreState`/`TransientState` → Ui/Pref/Keep/Ref.
