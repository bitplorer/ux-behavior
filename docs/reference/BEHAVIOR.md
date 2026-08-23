# Behavior 0.3 — standard product interface

> **Diátaxis:** reference · **Canonical:** `docs/reference/BEHAVIOR.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## Sync and async (first-class)

| API | Use |
|-----|-----|
| ``dispatch`` / ``submit`` / ``emit`` | **sync** actions only |
| ``async_dispatch`` / ``async_submit`` / ``async_emit`` | sync **or** async actions |

Wire attach prefers an **async** Channel handler so async ``@action`` works under ASGI.

## Dumb Host

```python
app = Behavior.boot("Shop")
app.add(Cart)
app.use("effects")
app.attach(asgi)
button(**app.control(cart.add, sku="x"))
```

## Caps / trust / preview

```python
@action(caps=())              # public
@action(caps=("orders.write",))  # protected offline

with app.trust(): ...
with app.preview(): ...       # blocks session/store writes
```

## Continuations

```python
follow_up("paid", "orders.confirm", args_from={"order_id": "id"})
app.emit("paid", id=42)
await app.async_emit("paid", id=42)
```

## Client risk

Money-shaped client paths (``price``, ``amount``, ``qty``, …) refuse by default.
``Behavior.boot(client_risk=False)`` to disable.

## Validation

Bad args → morph ``{action}.{field}-error`` (no exception to Host).
