# Migration — ux-app → ux-behavior

**Status:** Guidance for Hosts moving the author seat  
**Date:** 2026-08-18

---

## Why move

Same architectural laws (isolation, XOR, no fifth kernel, Caps, cold import).  
Clearer name, progressive disclosure, frozen public surface, Result builder, doctor.

## Import map

| ux-app | ux-behavior |
|--------|-------------|
| `from ux_app import App` | `from ux_behavior import Behavior` |
| `App.boot(...)` | `Behavior.boot(...)` |
| `from ux_app import Component, action` | same names from `ux_behavior` |
| `update` / `notify` / `go` | same |
| form outcome helpers | `submit_outcome(target, html, message=...)` |
| `from ux_app.overlay import open_overlay, close_overlay, select_region` | `from ux_behavior import open, close, select, confirm` |
| `from ux_app.adapter import compose, lower_morph` | `from ux_behavior.wire import compose, lower, Result` |
| `lower_morph(target, html)` | `lower(target, html)` or `Result().morph(...)` |
| (none) | `app.refresh("cart.badge")` |
| (none) | `from ux_behavior.isolation import doctor` |

## Overlay / chrome

```python
# before
from ux_app.overlay import open_overlay, close_overlay, select_region
ops = open_overlay("dialog", title="Edit")

# after
from ux_behavior import open, close, select, confirm
ops = open("dialog", title="Edit")
```

Visual Dialog/Sheet markup stays in **ux-dom**. Placement stays in the **Host**.

## Submit outcome

```python
from ux_behavior import submit_outcome

ops = submit_outcome("#address-form", html, message="Saved")
# → update(target) + optional notify(message)
```

## Live Result + motion

```python
# before
from ux_app.adapter import compose, lower_morph
ops = compose(lower_morph("#view", html), scene.play())

# after (preferred)
from ux_behavior.wire import Result
ops = Result().morph("#view", html).motion(scene.play()).build()

# after (equivalent low-level)
from ux_behavior.wire import compose, lower
ops = compose(lower("#view", html), scene.play())
```

XOR law is unchanged: morph(T) XOR scene.enter(T, html=) on one Result.

## What not to do

- Do not put `compose` / `lower` / `Result` on product top-level imports
- Do not invent a Host-local glue compositor
- Do not teach Channel `transition.*`
- Do not rename the product Host to "ux-host"

## Verify

```bash
pip install -e ".[dev]"
uxbehavior doctor --fail
pytest
```
