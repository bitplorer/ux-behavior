# Every mode matrix — offline / live / Caps / trust

This is the exhaustive **how to run behavior** guide. Same components; different **authority modes**.

Runnable tests: `tests/test_every_mode.py`.

---

## Mode axes

| Axis | Values |
|------|--------|
| **Network** | Offline (no Channel) · Live (`attach` + Channel) |
| **Caps on action** | Public `caps=()` · Protected `caps=("…",)` |
| **Authority** | Strict default · `trust()` · `_trusted=True` · wire attached |
| **Entry** | `dispatch` · `async_dispatch` · `submit` · `emit` · `control` |
| **Outcome** | Ops · morph error · `AuthorityError` · diagnostic |

---

## Shared components

```python
from ux_behavior import (
    Behavior, Component, MorphState, action, notify, follow_up, go,
    AuthorityError,
)

class Demo(Component):
    id = "demo"
    n = MorphState(0)

    def render(self):
        return f"<div id='demo'>{self.n}</div>"

    @action(caps=())
    def public_inc(self):
        self.n = int(self.n) + 1
        return None

    @action(caps=())
    def public_notify(self):
        return [notify("hello")]

    @action(caps=("demo.write",))
    def protected_set(self, n: int = 0):
        self.n = n
        return [notify(f"set {n}")]

    @action(caps=())
    def start_flow(self):
        follow_up("done", "demo.protected_set", n=9)
        return [notify("started")]

    @action(caps=())
    def typed(self, n: int = 0):
        self.n = n
        return None

    @action(caps=())
    async def public_async(self):
        self.n = int(self.n) + 10
        return None
```

---

## 1. Offline + public

```python
app = Behavior.boot(strict_caps=True)  # no attach
app.add(Demo)

ops = app.dispatch("demo.public_inc")
assert app.get("demo").n == 1
assert ops[0].pair == ("ui.dom", "morph")

ops = app.dispatch("demo.public_notify")
assert ops[0].pair == ("log", "append")

attrs = app.control(app.get("demo").public_inc)
assert attrs["data_action"] == "demo.public_inc"
assert attrs.get("data_cap", "") == ""  # offline: no Cap token
# diagnostic: CONTROL_OFFLINE
```

---

## 2. Offline + protected → refuse

```python
app = Behavior.boot(strict_caps=True)
app.add(Demo)

try:
    app.dispatch("demo.protected_set", n=3)
    assert False, "must refuse"
except AuthorityError as e:
    assert "Cap" in str(e)
    # diagnostic CAP_REQUIRED + hint
```

---

## 3. Offline + protected + trust()

```python
app = Behavior.boot(strict_caps=True)
app.add(Demo)

with app.trust():
    ops = app.dispatch("demo.protected_set", n=3)
assert app.get("demo").n == 3
# diagnostic TRUST_ON / TRUST_OFF
```

**Production:** never wrap normal HTTP handlers in `trust()`.

---

## 4. Offline + protected + `_trusted=True`

```python
app = Behavior.boot(strict_caps=True)
app.add(Demo)

ops = app.dispatch("demo.protected_set", n=4, _trusted=True)
assert app.get("demo").n == 4
```

Same power as trust for one call. Wire uses this **after** Channel verifies the request.

---

## 5. Offline + strict_caps=False

```python
app = Behavior.boot(strict_caps=False)
app.add(Demo)
# protected runs without Cap — dev only
app.dispatch("demo.protected_set", n=1)
```

---

## 6. Continuations offline

```python
app = Behavior.boot(strict_caps=True)
app.add(Demo)

app.dispatch("demo.start_flow")           # public; arms follow_up
app.emit("done")                          # runs protected_set with _trusted
assert app.get("demo").n == 9
```

`emit` always dispatches the continuation action as trusted (armed under an earlier authorized action). Still authenticate who may call `emit` on a network edge.

---

## 7. Validation morph (any mode)

```python
app = Behavior.boot()
app.add(Demo)
ops = app.dispatch("demo.typed", n="bad")  # type: ignore
assert ops[0].pair == ("ui.dom", "morph")
assert "error" in ops[0].payload["target"]
```

Does not raise to Host; returns error morphs.

---

## 8. Async offline

```python
import asyncio
app = Behavior.boot()
app.add(Demo)

# sync API rejects async action
try:
    app.dispatch("demo.public_async")
    assert False
except TypeError:
    pass

asyncio.run(app.async_dispatch("demo.public_async"))
assert app.get("demo").n == 10
```

---

## 9. Live path (Channel attached)

```python
app = Behavior.boot(strict_caps=True, strict_control=True, strict_attach=True)
app.add(Demo)
app.region(lambda: app.get("demo").render(), uid="app.root")

ch = app.attach(asgi)  # requires pip install ux-channel
if ch is None:
    print(app.diagnostics.last_hint())  # CHANNEL_MISSING or ATTACH_*
else:
    # control mints Cap via Channel
    attrs = app.control(app.get("demo").protected_set, n=1)
    assert "data_cap" in attrs or any("cap" in k.lower() for k in attrs)
    # inbound: Channel verifies → wire calls
    #   await async_dispatch(name, _trusted=True, **payload)
```

When `_wire` is set, Behavior treats protected actions as allowed at the Behavior layer (Channel already gated). Cap **crypto** remains Channel-only.

---

## 10. Live missing Channel

```python
app = Behavior.boot()
app.add(Demo)
ch = app.attach(asgi)  # ImportError path → None
assert ch is None
# CORE_CHANNEL_ABSENT / CHANNEL_MISSING in diagnostics
# protected still refused offline
```

---

## 11. submit helpers

```python
app = Behavior.boot()
app.add(Demo)
app.submit("demo.public_inc", {})
app.submit("demo.protected_set", {"n": 2}, _trusted=True)
```

---

## 12. Preview mode

```python
app = Behavior.boot()
app.add(Demo)
with app.preview():
    try:
        app.get("demo").n = 99  # session Morph write
        assert False
    except AuthorityError:
        pass
```

---

## Truth table (dispatch)

| caps | offline strict | trust/_trusted | attached wire | Result |
|------|----------------|----------------|---------------|--------|
| `()` | any | any | any | **runs** |
| non-empty | strict | no | no | **AuthorityError** |
| non-empty | strict | yes | no | **runs** |
| non-empty | strict | no | yes | **runs** (Channel gated) |
| non-empty | `strict_caps=False` | no | no | **runs** (dev) |

---

## Truth table (control)

| wire | mint | strict_control | Result |
|------|------|----------------|--------|
| no | — | any | offline attrs + CONTROL_OFFLINE |
| yes | ok | any | Cap attrs + CONTROL_MINTED |
| yes | fail | False | offline attrs + CONTROL_MINT_FAILED |
| yes | fail | True | **raises** |

---

## Copy-paste matrix runner

See `tests/test_every_mode.py` for automated coverage of rows above.
