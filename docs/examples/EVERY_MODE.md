# Every mode matrix — sync / async × offline / live × Caps / trust

Exhaustive **how to run** guide. Same components; every **entry** and **authority** combination.

Automated: `tests/test_every_mode.py`.

---

## Mode axes

| Axis | Values |
|------|--------|
| **Sync / async entry** | `dispatch` / `submit` / `emit` · `async_dispatch` / `async_submit` / `async_emit` |
| **Action kind** | Sync `@action` · Async `@action` (`async def`) |
| **Network** | Offline (no Channel) · Live (`attach` + Channel) |
| **Caps** | Public `caps=()` · Protected `caps=("…",)` |
| **Authority** | Strict default · `trust()` · `_trusted=True` · wire attached |
| **Outcome** | Ops · morph error · `AuthorityError` · `TypeError` · diagnostic |

---

## Shared components

```python
from ux_behavior import (
    Behavior, Component, MorphState, action, notify, follow_up,
    AuthorityError,
)

class Demo(Component):
    id = "demo"
    n = MorphState(0)

    def render(self):
        return f"<div id='demo'>{self.n}</div>"

    # ── sync actions ──
    @action(caps=())
    def public_inc(self):
        self.n = int(self.n) + 1
        return None

    @action(caps=("demo.write",))
    def protected_set(self, n: int = 0):
        self.n = n
        return [notify(f"set {n}")]

    @action(caps=())
    def start_flow(self):
        follow_up("done", "demo.protected_set", n=9)
        return [notify("started")]

    @action(caps=())
    def start_async_flow(self):
        follow_up("adone", "demo.protected_async_set", n=11)
        return [notify("started async flow")]

    @action(caps=())
    def typed(self, n: int = 0):
        self.n = n
        return None

    # ── async actions ──
    @action(caps=())
    async def public_async_inc(self):
        self.n = int(self.n) + 10
        return None

    @action(caps=("demo.write",))
    async def protected_async_set(self, n: int = 0):
        self.n = n
        return [notify(f"async set {n}")]
```

---

## Sync / async compatibility matrix

| Action kind | `dispatch` / `submit` / `emit` | `async_dispatch` / `async_submit` / `async_emit` |
|-------------|-------------------------------|--------------------------------------------------|
| **Sync** `@action def` | **runs** | **runs** (awaitable path calls sync fn) |
| **Async** `@action async def` | **`TypeError`** (use async_*) | **runs** |

**Rule:** async actions require async entry points. Sync actions run on both.

---

## Authority × entry (sync)

| caps | offline strict | trust / `_trusted` | `dispatch` |
|------|----------------|--------------------|------------|
| public | any | any | **runs** |
| protected | yes | no | **AuthorityError** |
| protected | yes | yes | **runs** |
| protected | `strict_caps=False` | no | **runs** (dev) |

Same rows for **`submit`**. Same Cap rules for **`emit`** target action (emit always passes `_trusted=True`).

---

## Authority × entry (async)

| caps | offline strict | trust / `_trusted` | `async_dispatch` |
|------|----------------|--------------------|------------------|
| public sync action | any | any | **runs** |
| public async action | any | any | **runs** |
| protected sync action | yes | no | **AuthorityError** |
| protected async action | yes | no | **AuthorityError** |
| protected sync/async | yes | yes | **runs** |
| async action via `dispatch` | any | any | **TypeError** |

Same Cap rows for **`async_submit`** / **`async_emit`**.

---

## Examples by mode

### S1 — Sync entry + sync public (offline)

```python
app = Behavior.boot(strict_caps=True)
app.add(Demo)
ops = app.dispatch("demo.public_inc")
assert app.get("demo").n == 1
app.submit("demo.public_inc", {})
assert app.get("demo").n == 2
```

### S2 — Sync entry + sync protected refuse (offline)

```python
try:
    app.dispatch("demo.protected_set", n=1)
except AuthorityError:
    pass
```

### S3 — Sync entry + sync protected + trust / _trusted

```python
with app.trust():
    app.dispatch("demo.protected_set", n=3)
app.dispatch("demo.protected_set", n=4, _trusted=True)
```

### S4 — Sync entry + sync protected continuation

```python
app.dispatch("demo.start_flow")
app.emit("done")  # protected_set via _trusted
assert app.get("demo").n == 9
```

### A1 — Async entry + sync public

```python
await app.async_dispatch("demo.public_inc")
await app.async_submit("demo.public_inc", {})
```

### A2 — Async entry + async public

```python
await app.async_dispatch("demo.public_async_inc")
assert app.get("demo").n == 10  # from 0
```

### A3 — Sync entry + async action → TypeError

```python
try:
    app.dispatch("demo.public_async_inc")
except TypeError as e:
    assert "async" in str(e).lower()
```

### A4 — Async entry + async protected refuse

```python
try:
    await app.async_dispatch("demo.protected_async_set", n=1)
except AuthorityError:
    pass
```

### A5 — Async entry + async protected + _trusted

```python
await app.async_dispatch("demo.protected_async_set", n=7, _trusted=True)
assert app.get("demo").n == 7
```

### A6 — Async entry + async protected + trust()

```python
with app.trust():
    await app.async_dispatch("demo.protected_async_set", n=8)
```

### A7 — Async emit continuation to async protected

```python
app.dispatch("demo.start_async_flow")  # sync arm
await app.async_emit("adone")           # async protected_async_set trusted
assert app.get("demo").n == 11
```

### A8 — Async emit continuation to sync protected

```python
app.dispatch("demo.start_flow")
await app.async_emit("done")
assert app.get("demo").n == 9
```

### V1 — Validation on sync and async entry

```python
ops = app.dispatch("demo.typed", n="bad")  # morph error
ops = await app.async_dispatch("demo.typed", n="bad")
```

### C1 — control() (always sync helper; Cap offline vs live)

```python
attrs = app.control(app.get("demo").public_inc)
# offline: data_action, empty data_cap
# live after attach: Channel Cap material when mint OK
```

### L1 — Live attach

```python
ch = app.attach(asgi)  # wire prefers async_dispatch for inbound
# protected inbound runs with _trusted after Channel auth
```

---

## Full truth table (copy)

| # | Entry | Action | Caps | Authority | Result |
|---|-------|--------|------|-----------|--------|
| 1 | dispatch | sync public | () | offline | runs |
| 2 | dispatch | sync protected | non-empty | offline strict | AuthorityError |
| 3 | dispatch | sync protected | non-empty | trust / _trusted | runs |
| 4 | dispatch | async any | any | any | TypeError |
| 5 | async_dispatch | sync public | () | offline | runs |
| 6 | async_dispatch | async public | () | offline | runs |
| 7 | async_dispatch | sync protected | non-empty | offline strict | AuthorityError |
| 8 | async_dispatch | async protected | non-empty | offline strict | AuthorityError |
| 9 | async_dispatch | sync/async protected | non-empty | trust / _trusted | runs |
| 10 | submit | (same as dispatch) | | | |
| 11 | async_submit | (same as async_dispatch) | | | |
| 12 | emit | target action | (trusted) | offline | runs target |
| 13 | async_emit | target sync/async | (trusted) | offline | runs target |
| 14 | control | — | — | offline | attrs, no Cap |
| 15 | control | — | — | live mint OK | Cap attrs |
| 16 | wire inbound | sync/async | protected | attached | async_dispatch + _trusted |

---

## Live note

After `attach`, Channel should call **`async_dispatch`** (or `async_submit`) so both sync and async actions work on the same edge. Behavior does not require Hosts to pick the entry style per action if the wire always uses the async API.
