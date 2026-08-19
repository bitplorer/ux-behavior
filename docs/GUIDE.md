# Guide — what ux-behavior is and how to use it

## Mental model (memorize this)

```text
Event        = named signal that happened          ("paid")
Action       = verb on a Component                 (@action)
Component    = unit: state + actions + render
Behavior     = root: register, dispatch, Ops, wire
Op           = instruction for UI/runtime
Wire         = optional door to ux-channel
```

**Behavior is not "Events".** Events may *trigger* actions; Behavior *runs* actions and produces Ops.

```text
You write     → Component + @action + MorphState/RefState
Root runs     → Behavior.dispatch / async_dispatch
Results       → list[Op]
Live path     → attach → Channel (Caps, transport)
Looks like    → ux-dom (optional)
Business data → your Host store (not this library)
```

## Install

```bash
pip install ux-behavior           # offline author + tests
pip install ux-behavior[channel]  # when you need live Caps (optional extra)
# or: pip install ux-channel
```

Hard dependency on Channel is **not** required. Missing Channel + protected Caps → fail closed.

## Minimal app

```python
from ux_behavior import Behavior, Component, MorphState, action, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return f"<div id='cart'>Items: {self.count}</div>"

    @action(caps=())  # public: no Cap required offline
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return None  # MorphState changed → auto morph

app = Behavior.boot(title="Shop")
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")
# ops == [Op(ui.dom, morph, {target: "cart", patch: "..."})]
```

## Everyday Host loop

```python
app = Behavior.boot("Shop")
app.add(Cart)
app.add(Chrome)
app.use("effects")              # optional stamp packs
# app.state.use("store", my_kv)  # optional Host storage
app.region(lambda: page_html())
app.attach(asgi)                # live; returns None if no Channel

# buttons
attrs = app.control(cart.add, sku="tee")
# offline: data_action + data_args
# live: Channel Cap mint when attach succeeded
```

## Sync vs async

| Call | Runs |
|------|------|
| `dispatch` / `submit` / `emit` | **Sync** `@action` only |
| `async_dispatch` / `async_submit` / `async_emit` | Sync **or** async `@action` |

```python
@action(caps=())
async def save(self):
    await db.flush()
    return None

await app.async_dispatch("cart.save")
```

Calling `dispatch` on an async action raises `TypeError` with a next-step hint.

## What returns from an action

| Return | Meaning |
|--------|--------|
| `None` | OK. If MorphState (public) fields changed → auto `update` morph |
| `Op` | Normalized to `[Op]` |
| `list[Op]` | Used as-is (stamp-checked) |
| anything else | `TypeError` |

RefState changes never trigger auto-morph.

## Caps in one paragraph

- `@action(caps=())` — public; runs offline.
- `@action(caps=("orders.write",))` — protected offline unless `app.trust()`, `_trusted=True`, or Channel is attached.
- Cap **crypto** is only in **ux-channel**. Behavior only enforces **policy**.
- Live: Channel authenticates the request; wire calls dispatch with trust.

## Continuations

```python
from ux_behavior import follow_up

@action(caps=())
def start_pay(self):
    follow_up("paid", "orders.confirm", args_from={"order_id": "id"})
    return [notify("complete payment")]

# later
app.emit("paid", id=42)  # runs orders.confirm(order_id=42)
```

`follow_up` only works **inside** an action during `dispatch`.

## Diagnostics

Nothing important is silent.

```python
app.diagnostics.summary()
app.diagnostics.last_hint()   # next step after last warn/error
app.diagnostics.has_errors()
```

Exceptions that subclass `BehaviorError` expose `.hint` when set.

## Doctor

```bash
uxbehavior doctor --fail
```

```python
from ux_behavior.isolation import doctor
assert doctor() == []
```

## Boundaries (do not put these in Behavior)

| Concern | Package |
|---------|--------|
| Cap HMAC / seal | ux-channel |
| Peer / world apply | ux-channel |
| HTML / tokens / Badge | ux-dom |
| Orders SQL / cart lines | Host domain store |
