# Modal / dialog

## State-owned modal

```python
from ux_behavior import Component, MorphState, action, notify

class ConfirmModal(Component):
    id = "modal.confirm"
    open = MorphState(False)
    title = MorphState("Confirm")
    body = MorphState("")

    def render(self):
        if not self.open:
            return "<div id='modal.confirm' hidden></div>"
        return f"""
        <div id="modal.confirm" role="dialog">
          <h2>{self.title}</h2>
          <p>{self.body}</p>
          <button data-act="cancel">Cancel</button>
          <button data-act="ok">OK</button>
        </div>"""

    @action(caps=())
    def show(self, title: str = "Confirm", body: str = ""):
        self.title = title
        self.body = body
        self.open = True
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        return None
```

## Chrome Ops (when Channel/product chrome listens)

```python
from ux_behavior import open, close

@action(caps=())
def show_help(self):
    return [open("modal.help")]

@action(caps=())
def hide_help(self):
    return [close("modal.help")]
```

## Modal + form submit

```python
from ux_behavior import submit_outcome

name = MorphState("")

@action(caps=())
def submit(self, name: str = ""):
    if not name.strip():
        return [update("modal.profile.name-error", "Required")]
    self.name = name.strip()
    self.open = False
    return submit_outcome("profile.card", f"<div id='profile.card'>{self.name}</div>", message="Saved")
```

## Focus trap / ESC

Browser responsibility: ESC → `modal.confirm.hide`. Behavior only holds `open`.
