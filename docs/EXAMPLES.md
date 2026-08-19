# Examples

## Public counter

```python
from ux_behavior import Behavior, Component, MorphState, action

class Counter(Component):
    id = "c"
    n = MorphState(0)

    def render(self):
        return f"<span id='c'>{self.n}</span>"

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
        return None

app = Behavior.boot()
app.add(Counter)
assert app.dispatch("c.inc")[0].pair == ("ui.dom", "morph")
```

## Ref does not morph

```python
from ux_behavior import RefState, action

class T(Component):
    id = "t"
    tick = RefState(0)
    def render(self):
        return "x"
    @action(caps=())
    def bump(self):
        self.tick = int(self.tick) + 1
        return None

app = Behavior.boot(); app.add(T)
assert app.dispatch("t.bump") == []
```

## Typed args → error morph

```python
@action(caps=())
def set_n(self, n: int = 0):
    self.n = n
    return None

ops = app.dispatch("c.set_n", n="bad")
assert "error" in ops[0].payload["target"]
```

## Continuation

```python
from ux_behavior import follow_up, notify

@action(caps=())
def start(self):
    follow_up("done", "c.inc")
    return [notify("wait")]

app.dispatch("c.start")
app.emit("done")
```

## Async action

```python
@action(caps=())
async def load(self):
    self.n = 1
    return None

await app.async_dispatch("c.load")
```

## Protected offline

```python
@action(caps=("x.write",))
def secure(self):
    return [notify("ok")]

# raises AuthorityError
# app.dispatch("c.secure")

with app.trust():
    app.dispatch("c.secure")
```

## Host store backend

```python
from ux_behavior import DictBackend
bag = DictBackend()
app.state.use("store", bag)
# MorphState(..., backend="store") reads/writes bag
```
