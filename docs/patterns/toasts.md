# Toasts / notices

## One-shot (preferred)

No Morph field — stamp `log.append` / notice drivers:

```python
from ux_behavior import notify

@action(caps=())
def save(self):
    # ...
    return [notify("Saved", level="info")]
```

Use when Channel/Host already renders a toast from `notify` / effects domain.

## Queue in UI (when you own the toast region)

```python
from ux_behavior import Behavior, Component, MorphState, RefState, action, update
import time

class Toasts(Component):
    id = "toasts"
    items = MorphState(())  # tuple of {id, message, level}
    _seq = RefState(0)

    def render(self):
        parts = []
        for it in self.items or ():
            parts.append(
                f"<div class='toast toast-{it["level"]}' data-id='{it["id"]}'>"
                f"{it['message']}"
                f"<button data-dismiss='{it['id']}'>x</button></div>"
            )
        return f"<div id='toasts'>{''.join(parts)}</div>"

    @action(caps=())
    def push(self, message: str = "", level: str = "info"):
        self._seq = int(self._seq or 0) + 1
        tid = str(self._seq)
        items = list(self.items or ())
        items.append({"id": tid, "message": message, "level": level})
        self.items = tuple(items)
        return None

    @action(caps=())
    def dismiss(self, id: str = ""):
        self.items = tuple(x for x in (self.items or ()) if x["id"] != id)
        return None

    @action(caps=())
    def clear(self):
        self.items = ()
        return None
```

## Auto-dismiss

Host JS timer posts `toasts.dismiss` with id, **or** continuation:

```python
from ux_behavior import follow_up

@action(caps=())
def push(self, message: str = "", level: str = "info"):
    ...
    follow_up(f"toast.expire.{tid}", "toasts.dismiss", id=tid)
    return None

# Host/ cron / Channel delayed event:
# app.emit(f"toast.expire.{tid}")
```

## Levels

`info` | `success` | `warning` | `error` — pass as `level` to `notify` or queue items.
