# Security model

> **Diátaxis:** reference · **Canonical:** `docs/reference/SECURITY.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## 1. Threat model (what Behavior assumes)

| Threat | Mitigation in Behavior | Mitigation elsewhere |
|--------|------------------------|----------------------|
| Unsigned button posts invoke privileged actions | Offline Cap refusal; live Cap verify | Channel Cap crypto |
| Client-writable bag holds prices/qty | `client_risk` path refuse | Channel ClientSafety |
| Preview/dry-run mutates authority state | `preview()` blocks session/store writes | Host |
| Stamp allows undeclared ops | `_check_stamp` PermissionError | Host agrees domains |
| Public dev secret in production | `attach()` raises `ATTACH_SECRET_REQUIRED` | Host env `UX_CHANNEL_SECRET` |
| Dev secret shared across processes | `REDIS_URL` with no configured secret raises, including when `DEBUG=1` | Set `UX_CHANNEL_SECRET` even in dev for `--workers` > 1, `--reload`, or Redis |
| Silent Cap-less controls in prod | `strict_control=True` | Host boot profile |

Behavior does **not** replace Channel. If Channel is absent, protected actions **do not run** (default).

## 2. Caps policy

### Declaration

```python
@action(caps=())                      # public
@action(caps=("orders.write",))       # requires authority offline
```

Semantics of the *strings* inside `caps` are **Host/Channel conventions**. Behavior stores and gates on non-emptiness; it does not interpret ACL graphs.

### Offline gate (`strict_caps=True`, default)

Protected action runs only if one of:

1. the wire passed the private trust sentinel after Channel accepted the Cap
2. `with app.trust():`
3. `app.dispatch_verified(name, payload)` or `await app.async_dispatch_verified(name, payload)` after Channel, or an equivalent check, has verified the Cap

Attaching a Channel does **not** skip this check (0.4.0). The Channel's own handler passes the sentinel only after it has verified the Cap. `True`, `"yes"`, and `1` are not that sentinel.

A `_trusted` key inside `submit(action, body)` or `async_submit(action, body)` does not grant trust. That dict is posted data. The same key is dropped from Channel payloads and from continuation slots. `dispatch(action, **body)` with `"_trusted"` in the body is ignored and logged.

Otherwise: `AuthorityError` + diagnostic `CAP_REQUIRED` + **hint**.

### Live gate

Channel verifies the Cap on the request **before** the wire handler runs. The wire then dispatches with the private sentinel. Behavior trusts the edge only after Channel has accepted the request.

Do not spread request JSON into `dispatch` or `submit`. A body that contains `_trusted` is caller data. Pass a payload dict to `submit(name, payload)` / `async_submit(name, payload)`, or pass the fields you mean as explicit keywords.

### trust() context <a id="trust-context"></a>

```python
with app.trust():
    ...
```

Scoped to the current context (contextvar, 0.4.0): other tasks and threads stay checked, and `strict_caps` is not changed. Emits diagnostic `TRUST_ON` / `TRUST_OFF`. Intended for **tests** and controlled Host admin tooling. Not for ordinary request handlers.

A task started inside `with app.trust()` keeps trust after the block ends.

> **Warning:** trust is carried by the current context. Tasks created inside the
> block (`asyncio.create_task`, `TaskGroup`, `loop.run_in_executor` with a copied
> context) copy that context and **inherit trust**, even after the block
> exits. Never start a long-lived worker, queue consumer, or background task
> inside `trust()`, because such a task keeps trust for its whole life.

### Follow-ups (`follow_up` / `emit`)

- A continuation fires **once per context**. After the first `emit`, a second
  `emit` of the same event in that context raises `ContinuationError`.
  Continuations live in a contextvar: tasks forked after arming each get their
  own copy, and separate requests cannot see or replay each other's follow-ups.
- Delivery is **at-most-once**. The continuation is removed *before* its action
  runs, so it is lost if that action fails or is refused (re-arm it to retry).
  This is intentional: a refund or payment step never runs twice.
- The continuation runs with the trust of the dispatch that armed it, or the
  emitter's own `trust()` context. `emit` never grants trust.
- A follow-up armed by an uncapped wire call is trusted by design. The wire
  grant is on the call, not on the action's `caps`. A public action invoked
  through that path arms its continuation as trusted.
- Only trusted host code may expose `emit` (for example, a webhook that has
  verified the provider's signature). Never route an unauthenticated request to
  `emit`: a continuation armed by trusted code would run with that trust.

## 3. control() and Cap mint

```python
app.control(component.method, **args) -> dict[str, str]
```

| Condition | Output |
|-----------|--------|
| Not attached | `data_action`, `data_args`, empty `data_cap` + `CONTROL_OFFLINE` |
| Attached, mint OK | Channel-provided attrs (includes Cap material) + `CONTROL_MINTED` |
| Attached, mint fails | Offline attrs + `CONTROL_MINT_FAILED`; **raises** if `strict_control` |

Production Hosts should set `strict_control=True` so a broken Cap path cannot ship Cap-less buttons quietly.

## 4. Client plane risk

When `client_risk=True` (default), writes to client-backed Morph fields whose **storage key** matches money-shaped patterns are refused:

```text
amount|price|qty|quantity|balance|money|cent|wallet|pay|cost|total|sku
```

Raise: `AuthorityError` with hint to use `store`/`session` or Host domain data.

Disable only for specialized Hosts: `Behavior.boot(client_risk=False)`.

## 5. Preview mode

```python
with app.preview():
    ...
```

Blocks **session** and **store** plane writes. Client and Ref remain writable so dry-run UI can still flip themes / internal ticks.

## 6. Secrets

| Variable | Role |
|----------|------|
| `UX_CHANNEL_SECRET` | Preferred Channel secret |
| `UX_BEHAVIOR_SECRET` | Fallback |
| `DEBUG` | `1` / `true` / `yes` / `on` (strip + lower) selects one random per-process secret when both secrets above are unset. Read it with `ux_behavior.wire.debug_requests_dev(env=None)`; the set is `ux_behavior.wire.DEBUG_TRUTHY` |
| public dev string | Never accepted, in production or dev, including `ChannelConfig.production` when `REDIS_URL` is set |

Outside dev, `attach()` with no secret raises. It does not sign with a built-in constant. `REDIS_URL` with no configured secret raises even when `DEBUG=1`. Set `UX_CHANNEL_SECRET` even in dev when using `--workers` greater than 1, `--reload`, or `REDIS_URL`. The per-process secret does not survive a restart, and a Cap minted in one process is refused by another. Production: set a strong secret via the environment or a process secrets manager **before** attach.

## 7. Recommended production boot flags

```python
Behavior.boot(
    title="…",
    strict_caps=True,
    client_risk=True,
    strict_control=True,
    strict_attach=True,
    developer_hints=False,
)
```

## 8. What Hosts must still do

- Authorize **domain** operations (inventory, charges) in Host services — Caps on UI actions are not a substitute for server-side business authorization.
- Configure Channel client **allowlists** for preference keys.
- Never log Cap tokens.
