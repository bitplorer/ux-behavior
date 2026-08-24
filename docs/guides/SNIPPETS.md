# ux-behavior — snippets

> **Diátaxis:** how-to · copy-paste patterns from the public API (`__all__` / CLI).
> Map: see this package `docs/INDEX.md`.

Product behavior. Component + @action + Morph/Ref → verified list[Op].

Every block is meant to run (or to be the exact fragment you drop into a running app). Names are public exports. If code and this page disagree, **code wins**.

**13 snippets** covering install, core usage, fail-closed errors, live/async, CLI, and the usage patterns that keep layers from leaking.

### Public names in this cookbook

`Behavior`, `Component`, `MorphState`, `RefState`, `action`, `notify`, `update`, `go`, `open`, `close`, `confirm`, `select`, `submit_outcome`, `AuthorityError`, `follow_up`, `bind`, `UiState`, `PrefState`, `KeepState`, `DictBackend`, `ValidationError`, `doctor`

## Contents

- [Install](#beh-install)
- [Component, MorphState, @action, dispatch](#beh-core)
- [Ops macros: update, notify, go, chrome](#beh-ops)
- [control() attrs + bind / .ui](#beh-control)
- [follow_up + emit continuations](#beh-follow-up)
- [bind() / .ui() preferred over control(str)](#beh-bind)
- [UiState / PrefState / KeepState planes](#beh-planes)
- [StateAPI + DictBackend](#beh-state-api)
- [submit, emit, refresh, actions](#beh-submit-emit)
- [async_dispatch and tests-only trust()](#beh-async-trust)
- [ValidationError on @action args](#beh-validation)
- [Isolation Law doctor](#beh-isolation)
- [Pattern: MorphState vs RefState](#beh-pattern-morph-ref)


## Install

### Install

<a id="beh-install"></a>

Python ≥ 3.10. Isolation Law: cold import does not load Channel.

```bash
pip install ux-behavior
pip install "ux-behavior[channel]"   # optional live Caps
uxbehavior doctor --fail
```


## Core usage

### Component, MorphState, @action, dispatch

<a id="beh-core"></a>

MorphState = must repaint. RefState = silent. Empty caps = public. Non-empty caps need a live Cap or tests-only trust().

```python
from ux_behavior import Behavior, Component, MorphState, RefState, action, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")   # silent — does not by itself demand a morph

    def render(self):
        return f"<div id='cart'>{self.count} {self.last_sku}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last_sku = sku
        return [notify(f"Added {sku}")]

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Checkout")]

app = Behavior.boot("Shop", strict_caps=True)
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")   # public
print(ops)
# app.dispatch("cart.checkout")             # AuthorityError offline
```

### Ops macros: update, notify, go, chrome

<a id="beh-ops"></a>

@action must return list[Op] | Op | None. Chrome verbs (open/close/select/confirm) expand to legal op pairs.

```python
from ux_behavior import action, notify, update, go, open, close, confirm, select, submit_outcome

@action(caps=())
def save(self):
    return submit_outcome("#cart", self.render(), message="Saved")

@action(caps=())
def sheet(self):
    return list(open("sheet", key="cart")) + [notify("Opened")]

@action(caps=())
def jump(self):
    return [go("/orders")]
```

### control() attrs + bind / .ui

<a id="beh-control"></a>

control() emits button/form attrs. When Channel is attached, Caps are minted into those attrs.

```python
from ux_behavior import Behavior, Component, action

class Cart(Component):
    id = "cart"

    @action(caps=())
    def add(self, sku: str = ""):
        return []

app = Behavior.boot("Shop", strict_caps=False)
cart = app.add(Cart)
print(app.control("cart.add", sku="tee"))
# preferred author path when you have the method:
print(cart.add.ui(sku="tee"))
```

### follow_up + emit continuations

<a id="beh-follow-up"></a>

Continuations are explicit. Do not mutate from a notify callback — that is NestedTransactionError on the data plane, and ContinuationError here if misused.

```python
from ux_behavior import action, follow_up, notify

@action(caps=())
def add(self, sku: str = ""):
    self.count = int(self.count) + 1
    return [notify("Added"), follow_up("cart.refresh")]

# Later / elsewhere:
# app.emit("cart.refresh")
```

### bind() / .ui() preferred over control(str)

<a id="beh-bind"></a>

bind / .ui fail closed on unknown kwargs. control('cart.add') is the stringly escape hatch.

```python
from ux_behavior import Behavior, Component, MorphState, action, bind, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return f"<button id='cart' {self._attrs()}>{self.count}</button>"

    def _attrs(self):
        # preferred: symbol-safe
        parts = bind(self.add, sku="tee")
        return " ".join(f'{k}="{v}"' for k, v in parts.items())

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify(f"Added {sku}")]

app = Behavior.boot("Shop", strict_caps=False)
cart = app.add(Cart)
print(bind(cart.add, sku="tee"))
print(cart.add.ui(sku="tee"))     # same attrs
```

### UiState / PrefState / KeepState planes

<a id="beh-planes"></a>

MorphState ≈ useState (may demand a morph). RefState ≈ useRef (silent). Hosts wire backends via app.state.use(plane, backend).

```python
from ux_behavior import Component, MorphState, RefState, UiState, PrefState, KeepState

class Settings(Component):
    id = "settings"
    open_ = UiState(False)          # session — MorphState(backend="session")
    theme = PrefState("system")     # client  — MorphState(backend="client")
    draft = KeepState("")           # store   — MorphState(backend="store")
    last_sku = RefState("")         # silent  — never auto-morphs
    count = MorphState(0)           # default session
```

### StateAPI + DictBackend

<a id="beh-state-api"></a>

Host owns storage policy. Channel attach calls use(..., lock=False) for still-unlocked planes.

```python
from ux_behavior import Behavior, DictBackend

app = Behavior.boot("Shop", strict_caps=False)
app.state.use("session", DictBackend(), lock=True, source="host")
app.state.use("store", DictBackend({"seed": 1}), lock=True)
print(app.state.report())
# After Behavior.attach, Channel may install defaults for *unlocked* planes only.
# Host lock=True wins.
```

### submit, emit, refresh, actions

<a id="beh-submit-emit"></a>

submit is dispatch with an args dict. emit resolves follow_up continuations. refresh() re-renders one component.

```python
from ux_behavior import Behavior, Component, MorphState, action, follow_up, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return f"<div id='cart'>{self.count}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify("Added"), follow_up("cart.refresh")]

    @action(caps=())
    def refresh(self):
        return []

app = Behavior.boot("Shop", strict_caps=False)
app.add(Cart)
print(app.actions("cart"))                 # ['cart.add', 'cart.refresh']
print(app.submit("cart.add", {"sku": "tee"}))
print(app.emit("cart.refresh"))            # continuation, trusted
print(app.refresh("cart"))                 # morph from render()
print(app.get("cart").count)
```


## Fail closed

### async_dispatch and tests-only trust()

<a id="beh-async-trust"></a>

dispatch() refuses async handlers (no nested event loop). trust() is a test door, not a production bypass.

```python
import asyncio
from ux_behavior import AuthorityError

app = Behavior.boot("Shop", strict_caps=True)
app.add(Cart)

try:
    app.dispatch("cart.checkout")
except AuthorityError as exc:
    print("offline cap", exc)

async def main():
    async with app.trust():          # tests only — never in product
        await app.async_dispatch("cart.checkout")

asyncio.run(main())
```

### ValidationError on @action args

<a id="beh-validation"></a>

Unknown kwargs to .ui() also fail closed. Do not coerce types silently — type= on MorphState is exact class match.

```python
from ux_behavior import Behavior, Component, action, ValidationError

class Cart(Component):
    id = "cart"

    @action(caps=())
    def add(self, sku: str):
        return []

app = Behavior.boot("Shop", strict_caps=False)
app.add(Cart)
# missing required sku → ValidationError (or validation ops, depending on finish path)
try:
    app.dispatch("cart.add")
except (ValidationError, TypeError) as exc:
    print(type(exc).__name__, exc)
```


## CLI

### Isolation Law doctor

<a id="beh-isolation"></a>

uxbehavior doctor --fail is the CLI. Product code must not import ux_channel outside the wire/ door.

```python
from ux_behavior.isolation import doctor

assert doctor() == []   # cold import must not load Channel
```


## Usage patterns

### Pattern: MorphState vs RefState

<a id="beh-pattern-morph-ref"></a>

If the user cannot see it, it is not MorphState. Auto-morph on MorphState+None return is a convenience, not a second state system.

```python
from ux_behavior import Component, MorphState, RefState, action, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)     # changing this means the region must repaint
    last_sku = RefState("")   # changing this does not by itself demand a morph

    @action(caps=())
    def add(self, sku: str = ""):
        self.last_sku = sku          # silent
        self.count = int(self.count) + 1
        return [notify(f"Added {sku}")]
```
