# 05 — Caps and trust

## Public vs protected

```python
@action(caps=())
def open_menu(self):
    self.menu_open = True
    return None

@action(caps=("orders.write",))
def place(self, sku: str = ""):
    return [notify("placed")]
```

Offline without Channel:

```python
app.dispatch("chrome.open_menu")          # OK
app.dispatch("orders.place", sku="x")     # AuthorityError + diagnostics CAP_REQUIRED
```

## Testing protected actions

```python
with app.trust():
    app.dispatch("orders.place", sku="x")

# or
app.dispatch("orders.place", sku="x", _trusted=True)
```

Never use `trust()` on production request paths.

## Live

After `app.attach(asgi)`, Channel authenticates inbound events; wire calls dispatch with trust. Cap **mint** happens in `app.control(...)`.
