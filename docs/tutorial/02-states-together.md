# 02 — Using different states together

## Goal

One component with **session UI**, **client prefs**, **store draft**, and **silent Ref** — and knowing which writes repaint.

## Rules (explicit)

| Field API | Backend | Auto-morph on `return None`? |
|-----------|---------|------------------------------|
| `MorphState` | session / client / store | **Yes** if value changed |
| `RefState` | instance only | **Never** |

```python
from ux_behavior import (
    Behavior, Component, MorphState, RefState,
    UiState, PrefState, KeepState, action,
)

class Workspace(Component):
    id = "ws"

    # Session — navigation / open panels (per browser session bag)
    page = MorphState("home")                 # backend="session" default
    menu_open = UiState(False)                # sugar = session Morph

    # Client — durable prefs (theme); may map to Channel client when attached
    theme = PrefState("system", key="ui.theme")

    # Store — Host can plug Redis/kv via app.state.use("store", ...)
    draft = KeepState("")

    # Ref — internal counters / tokens; never drive morph by themselves
    render_ticks = RefState(0)

    def render(self):
        self.render_ticks = int(self.render_ticks or 0) + 1  # silent
        return (
            f"<section id='ws' data-page='{self.page}' data-theme='{self.theme}'>"
            f"<p>menu={'open' if self.menu_open else 'closed'}</p>"
            f"<pre>{self.draft}</pre>"
            f"</section>"
        )

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        self.menu_open = False
        return None  # morph: page + menu_open changed

    @action(caps=())
    def set_theme(self, theme: str = "system"):
        self.theme = theme
        return None  # morph: client field still participates in dirty

    @action(caps=())
    def save_draft(self, text: str = ""):
        self.draft = text
        return None  # morph: store field dirty

    @action(caps=())
    def touch_ref_only(self):
        self.render_ticks = int(self.render_ticks or 0) + 1
        return None  # NO morph — only Ref changed

app = Behavior.boot()
ws = app.add(Workspace)

assert app.dispatch("ws.go", page="settings")
assert ws.page == "settings"
assert ws.menu_open is False

assert app.dispatch("ws.set_theme", theme="dark")
assert app.state.backend("client").data.get("ui.theme") == "dark"

assert app.dispatch("ws.save_draft", text="hello")
assert app.state.backend("store").data.get("ws.draft") == "hello"

assert app.dispatch("ws.touch_ref_only") == []  # empty Ops
assert int(ws.render_ticks) >= 1
```

## Mixing backends on purpose

```text
User clicks "Settings"
  → session.page = "settings"     (morph shell)
  → maybe client.theme unchanged
  → store.draft kept across pages
  → Ref tick never alone causes morph
```

## Host plugs durable store

```python
from ux_behavior import DictBackend

kv = DictBackend()
app.state.use("store", kv)  # all KeepState / backend="store" fields use kv
app.dispatch("ws.save_draft", text="persisted")
assert kv.data["ws.draft"] == "persisted"
```

## Client risk (money paths)

```python
# This raises AuthorityError by default:
# bad = MorphState(0, backend="client", key="cart.price")
# Prefer store/session or Host domain DB for money.
```
