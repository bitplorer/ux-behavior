# Behavior — standard product interface

Dumb Host shape::

```python
app = Behavior.boot("Shop")
app.add(Cart)
app.use("effects")
app.attach(asgi)
# buttons
button(**app.control(cart.add, sku="x"))
# server path is Channel → trusted dispatch
```

## Caps

- ``@action(caps=())`` public
- ``@action(caps=("orders.write",))`` protected
- Offline: refuse unless ``app.trust()`` / ``_trusted=True`` / attached wire
- Live wire dispatch is trusted after Channel auth

## Async

```python
@action(caps=())
async def save(self): ...
await app.async_dispatch("cart.save")
```

## Validation

Bad / mistyped args → morph targets ``{action}.{field}-error`` (no exception to Host).

## Preview

```python
with app.preview():
    # session/store writes refuse; safe for dry-run UI
```

## Continuations

```python
follow_up("paid", "orders.confirm", order_id=1)
app.emit("paid")
```
