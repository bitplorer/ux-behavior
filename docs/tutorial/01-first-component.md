# 01 — First component

## Goal

A counter that morphs on click. No Channel required.

## Full file

```python
from ux_behavior import Behavior, Component, MorphState, action

class Counter(Component):
    id = "counter"
    n = MorphState(0)

    def render(self):
        # target id should match component id for update()
        return f"<div id='counter'><span>{self.n}</span></div>"

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
        return None  # MorphState changed → Behavior issues ui.dom.morph

app = Behavior.boot(title="Demo")
app.add(Counter)

ops = app.dispatch("counter.inc")
assert len(ops) == 1
assert ops[0].pair == ("ui.dom", "morph")
assert ops[0].payload["target"] == "counter"
assert "1" in str(ops[0].payload["patch"])

ops2 = app.dispatch("counter.inc")
assert "2" in str(ops2[0].payload["patch"])
```

## What just happened

1. `Behavior.boot` creates the root (memory planes, diagnostics).
2. `add(Counter)` instantiates and binds `_behavior`.
3. `dispatch("counter.inc")` runs the method.
4. `return None` + `n` changed → `refresh("counter")` → `update("counter", html)`.

## Try yourself

```python
print(app.get("counter").n)
print(app.actions())
print(app.diagnostics.summary())
```
