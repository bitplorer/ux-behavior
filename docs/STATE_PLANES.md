# MorphState vs NoMorphState

```python
from ux_behavior import MorphState, NoMorphState

page  = MorphState("home")                              # backend="session"
step  = MorphState(1, backend="store")
theme = MorphState("system", backend="client", key="ui.theme")
n     = MorphState(0, seal=int)                         # opt-in strict
token = NoMorphState(None)                              # never auto-morph
```

## Effect split

| Kind | `return None` after change |
|------|----------------------------|
| **MorphState** | dirty → `render()` → morph |
| **NoMorphState** | no auto-morph |

## `backend=`

| Value | Meaning |
|-------|---------|
| `"session"` (default) | UI chrome bag / Channel session after attach |
| `"client"` | Pref bag / Channel client after attach |
| `"store"` | Component keep bag |
| `PlaneBackend` instance | Field-local custom storage |

Host-wide: `app.set_plane_backend("store", kv_backend)` (locks against attach overwrite).

## `seal=`

Opt-in. `seal=int` → exact type, no coerce. Or pass a callable validator.

Aliases: `SessionState` / `ClientState` / `StoreState` / `TransientState` → same factories.
