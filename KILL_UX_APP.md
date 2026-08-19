# Kill ux-app — ownership map

## Field markers

| ux-app | ux-behavior |
|--------|-------------|
| `Session(...)` | **`SessionState(...)`** |
| `Client(...)` | **`ClientState(...)`** |
| `Store(...)` | **`StoreState(...)`** |
| `Transient(...)` | **`TransientState(...)`** |

Bare `Session` / `Client` / `Store` / `Transient` are **banned** (collision with HTTP/Channel words). The plane names stay; **State** marks them as component fields.

```python
from ux_behavior import Component, SessionState, ClientState

class Chrome(Component):
    id = "chrome"
    page = SessionState("home")
    theme = ClientState("system", key="ui.theme")
```

## Feature → owner

| ux-app | Owner |
|--------|--------|
| `App` | `Behavior` |
| Ops / chrome verbs | ux-behavior |
| Field planes | ux-behavior (`*State`) |
| Cap mint / verify | ux-channel |
| Markup | ux-dom |
| Page shell / `finish` / `act` | Host |
