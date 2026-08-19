# 03 — Actions and Ops

## Return contract

```python
from ux_behavior import action, update, notify, go, open, close, submit_outcome

@action(caps=())
def only_state(self):
    self.page = "x"
    return None          # auto morph if Morph dirty

@action(caps=())
def explicit(self):
    return [update("ws", "<div id='ws'>hi</div>"), notify("saved")]

@action(caps=())
def navigate(self):
    return [go("/cart")]

@action(caps=())
def chrome(self):
    return [open("modal.help")]  # product chrome verb

@action(caps=())
def after_submit(self):
    return submit_outcome("form.box", "<p>ok</p>", message="Done")
```

## Stamp

Ops are checked against the session stamp. Unknown pairs raise `PermissionError`.

```python
app.use("effects")   # adds ui.notice.* if you emit those pairs
app.domain("orders", "1", [("orders", "place")])
```

Default stamp always includes `ui.dom.morph`, `log.append`, `nav.push`, `kv.*`.
