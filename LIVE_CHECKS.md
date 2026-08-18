# Live checks — 2026-08-19

## Environment

| Package | Present |
|---------|---------|
| ux-behavior | yes (editable) |
| ux-channel | **yes** (`python/` subdir install) |
| ux-dom | no (not required for these checks) |
| FastAPI | yes (for ASGI attach) |

## Results

| Check | Result |
|-------|--------|
| Cold import `ux_behavior` | ok |
| `probe()` with Channel installed | `{"ux_dom": false, "ux_channel": true}` |
| `present()` | `True` |
| `dispatch("cart.add")` dirty → refresh | ok — returns morph Op |
| `attach(app, None)` | `None` (correct) |
| `attach(app, FastAPI())` | **Channel** instance; `attached=True` |
| Idempotent second attach | returns same wire |
| Isolation `uxbehavior doctor --fail` | ok |

## Friction notes

1. **Channel install path** is `git+.../ux-channel.git#subdirectory=python` — Hosts must document that.
2. **Attach requires a real ASGI app** (FastAPI). Without it, soft-fail is correct.
3. **Harbor still depends on ux-app** (`finish`, `open_overlay`, `Session`, `act`/`wire` helpers). Pilot maps one component pattern only; full harbor swap is multi-file.
4. **ux-dom not required** for wire attach or dispatch tests.

## Harbor pilot scope (recommended first screen)

**Cart / bag** (`app/screens/bag.py`) is the best first target:

| Harbor (ux-app) | ux-behavior |
|-----------------|-------------|
| `Component` + methods | `Component` + `@action` |
| `finish(open_overlay(...))` | `open("sheet", key="cart")` + optional `notify` |
| `Session("")` fields | plain instance attrs + dirty projection |
| `go("cart")` | `go("/cart")` or Host route helper |
| `host = App.boot` | `Behavior.boot` + `attach(asgi)` |

See `examples/harbor_cart_pilot.py` for a minimal parallel implementation.
