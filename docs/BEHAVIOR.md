# Behavior — standard product interface

## Who is who

| Role | API |
|------|-----|
| Unit | `Component` |
| Verb | `@action` |
| Root | `Behavior` |
| Signal | event name + `follow_up` / `emit` |
| Fields | `MorphState` / `RefState` |
| Storage | `app.state.use` |
| Live | `attach` / `control` (wire → Channel) |

## Caps

```python
@action(caps=("orders.write",))
 def place(self): ...

@action(caps=())   # public
 def open_menu(self): ...
```

- Offline + `strict_caps=True` (default): protected actions need `_trusted=True` or Channel attach.
- Live: Cap verified on the wire before dispatch.

## Continuations

```python
@action(caps=())
def start(self):
    follow_up("paid", "orders.confirm", order_id=1)
    return [notify("pay now")]

app.emit("paid")   # runs orders.confirm
```

## Domains

```python
app.use("effects")  # stamps ui.notice.*
app.use("search")
```

Drivers still apply on Channel; stamp is the author agreement.
