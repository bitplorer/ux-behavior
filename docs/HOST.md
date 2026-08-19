# Host cookbook (production)

## Recommended boot

```python
from ux_behavior import Behavior

app = Behavior.boot(
    "Shop",
    strict_caps=True,
    client_risk=True,
    strict_control=True,   # no silent Cap-less buttons in prod
    strict_attach=True,    # fail loud if Channel boot fails
)
app.add(Cart)
app.add(Chrome)
app.use("effects")
app.state.use("store", production_kv)  # lock Host store
app.region(lambda: render_page(app), uid="app.root")
ch = app.attach(asgi)
assert ch is not None
assert app.cores_available["ux_channel"]
```

## Button rendering

```python
def add_button(cart):
    return button("Add", **app.control(cart.add, sku=sku))
```

## Domain data

Keep cart lines / orders in **your** store. Behavior fields are UI/session/client prefs and small drafts — not the source of truth for money.

## Observability

```python
# after request
if app.diagnostics.has_errors():
    log.error(app.diagnostics.summary())
```

## Tests

```python
app = Behavior.boot(strict_caps=True)
app.add(Cart)
with app.trust():
    app.dispatch("orders.place", **payload)  # protected offline

# or public actions only
@action(caps=())
def open_menu(self): ...
```

## Kill ux-app checklist

- [ ] Components + actions on Behavior  
- [ ] MorphState/RefState + app.state  
- [ ] control/dispatch/attach  
- [ ] follow_up/emit if needed  
- [ ] Channel for Caps  
- [ ] ux-dom for markup  
- [ ] Host domain store for business data  
