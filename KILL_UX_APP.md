# Kill ux-app — ownership map

**Goal:** Hosts run on **ux-behavior + ux-channel + ux-dom** only.

## Field markers (ux-behavior way)

| ux-app | ux-behavior | Intent |
|--------|-------------|--------|
| `Session(...)` | **`ui_state(...)`** | UI chrome / screen state |
| `Client(...)` | **`pref(...)`** | Browser preference |
| `Store(...)` | **`persist(...)`** | Component-local kept value |
| `Transient(...)` | **`flash(...)`** | Instance-only |
| `Sealed` | ordinary attrs | Dropped |

`Session` is **banned** — collides with HTTP/Channel session.

```python
from ux_behavior import Component, ui_state, pref, persist, flash

class Chrome(Component):
    id = "chrome"
    page = ui_state("home")
    menu_open = ui_state(False)
    theme = pref("system", key="ui.theme")
```

## Feature → owner

| ux-app feature | Owner |
|----------------|--------|
| `App` | **ux-behavior** `Behavior` |
| `Component` + `@action` | **ux-behavior** |
| Ops + overlay helpers | **ux-behavior** |
| Field markers | **ux-behavior** (`ui_state` / `pref` / `persist` / `flash`) |
| Domain stamp | **ux-behavior** |
| Peer drivers | **Channel / Host** |
| Cap mint / verify | **ux-channel** |
| `control` | **ux-behavior** → Channel when attached |
| Markup / Badge | **ux-dom** |
| Page shell / `finish` / `act` | **Host** |

## Harbor cutover

1. Imports → `ux_behavior`
2. `Session` → `ui_state`
3. `App.boot` → `Behavior.boot` + `attach`
4. Keep Host `finish` / `act` / `wire`
5. Drop ux-app dependency
