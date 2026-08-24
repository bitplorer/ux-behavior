# Start here — ux-behavior

**Audience:** first-time users of this package.
**Promise:** one Component + action dispatch in five minutes.
**Time:** ~5 minutes.

Kept short start: [START.md](START.md). Tutorial: [docs/tutorial/](docs/tutorial/README.md).
**Map:** [docs/INDEX.md](docs/INDEX.md). Binding design: [DESIGN.md](DESIGN.md).
**Cookbook:** [docs/guides/SNIPPETS.md](docs/guides/SNIPPETS.md) — Component, @action, Morph/Ref, bind/.ui, planes, continuations.

---

## 1. What this layer is (and is not)

> Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.

| Owns | Does **not** own |
|------|------------------|
| `Behavior`, `Component`, `MorphState` / `RefState`, `@action` | HTML trees / Document (`ux-dom`) |
| Validation, continuations, chrome verbs | Wire codecs / Cap crypto (`ux-channel`) |
| Isolation Law (cold import loads no Channel) | Motion IR (`ux-motion`) |
| | Product create-app / serve (`ux-compose`) |

Day-1 never sees the wire door. Progressive: `from ux_behavior.wire import Result`.

---

## 2. Five minutes

```bash
pip install ux-behavior
# or from this tree:
pip install -e ".[dev]"
```

```python
from ux_behavior import Behavior, Component, MorphState, action, notify

class CartBadge(Component):
    id = "cart.badge"
    count = MorphState(0)

    def render(self):
        return f"<button id='cart.badge'>{self.count}</button>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify("Added")]

app = Behavior.boot(title="Cart")
app.add(CartBadge)
print(app.dispatch("cart.badge.add", sku="tee"))
print(list(app.components().keys()))  # ['cart.badge']
```

Success: a `list` of Ops including a notify, and `cart.badge` in the component map.

Chrome verbs:

```python
from ux_behavior import open, close, select, confirm

ops = open("dialog", title="Edit address")
ops = select("orders.tabs", "shipped")
ops = confirm("Delete?", body="Cannot undo.")
ops = close()
```

Doctor:

```python
from ux_behavior.isolation import doctor
assert doctor() == []
```

```bash
uxbehavior doctor --fail
```

---

## 3. Progressive door (not day-1)

```python
from ux_behavior.wire import Result, Conflict

ops = (
    Result()
    .morph("#view", html)          # authority morph (idiomorph)
    .motion(scene.play())          # no html on #view — XOR enforced
    .navigate("/cart")             # ordered last
    .build()
)
```

Illegal (raises `Conflict`): `Result().morph("#view", html).motion(scene_with_html_on_view).build()`.

These names are **not** on top-level `__all__`. That friction is intentional.

---

## 4. Where next

| Goal | Doc |
|------|-----|
| Tutorial (01–10) | [docs/tutorial/](docs/tutorial/README.md) |
| Guide | [docs/GUIDE.md](docs/GUIDE.md) |
| API surface | [docs/API.md](docs/API.md) |
| State planes | [docs/STATE_DEEP.md](docs/STATE_DEEP.md) |
| UI patterns | [docs/patterns/](docs/patterns/README.md) |
| Offline/online × Caps | [docs/examples/EVERY_MODE.md](docs/examples/EVERY_MODE.md) |
| Binding design | [DESIGN.md](DESIGN.md) |
| Migration from ux-app | [MIGRATION.md](MIGRATION.md) |
| Contributor / agent | [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md) |
| Full map | [docs/INDEX.md](docs/INDEX.md) |
