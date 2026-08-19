# Confirm flows

## Inline confirm modal + target

```python
from ux_behavior import Component, MorphState, RefState, action, notify

class DeleteFlow(Component):
    id = "delete.flow"
    open = MorphState(False)
    target_id = RefState("")  # silent

    def render(self):
        if not self.open:
            return "<div id='delete.flow' hidden></div>"
        return f"""
        <div id="delete.flow" role="dialog">
          Delete {self.target_id}?
          <button data-act="cancel">Cancel</button>
          <button data-act="confirm">Delete</button>
        </div>"""

    @action(caps=())
    def ask(self, id: str = ""):
        self.target_id = id
        self.open = True
        return None

    @action(caps=())
    def cancel(self):
        self.open = False
        self.target_id = ""
        return None

    @action(caps=("items.delete",))
    def confirm(self):
        tid = self.target_id
        self.open = False
        self.target_id = ""
        # Host domain delete(tid)
        return [notify(f"Deleted {tid}")]
```

## chrome.confirm Op

```python
from ux_behavior import confirm
return [confirm("Delete item?", action="delete.flow.confirm")]
```

When product chrome handles `confirm` pairs.
