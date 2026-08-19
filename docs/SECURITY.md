# Security model

## 1. Threat model (what Behavior assumes)

| Threat | Mitigation in Behavior | Mitigation elsewhere |
|--------|------------------------|----------------------|
| Unsigned button posts invoke privileged actions | Offline Cap refusal; live Cap verify | Channel Cap crypto |
| Client-writable bag holds prices/qty | `client_risk` path refuse | Channel ClientSafety |
| Preview/dry-run mutates authority state | `preview()` blocks session/store writes | Host |
| Stamp allows undeclared ops | `_check_stamp` PermissionError | Host agrees domains |
| Dev secret in production | `ATTACH_DEV_SECRET` diagnostic | Host env |
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

1. `dispatch(..., _trusted=True)`
2. `with app.trust():`
3. `app._wire is not None` (attached)

Otherwise: `AuthorityError` + diagnostic `CAP_REQUIRED` + **hint**.

### Live gate

Channel verifies the Cap on the request **before** the wire handler runs. Wire then calls:

```python
await behavior.async_dispatch(name, _trusted=True, **payload)
```

Behavior trusts the edge only after Channel has accepted the request. **Do not** expose `_trusted=True` on public HTTP handlers without Channel.

### trust() context

```python
with app.trust():
    ...
```

Emits diagnostic `TRUST_ON` / `TRUST_OFF`. Intended for **tests** and controlled Host admin tooling. Not for ordinary request handlers.

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
| built-in dev string | Only if both unset → `ATTACH_DEV_SECRET` warn |

Production: set a strong secret via environment or process secrets manager **before** attach.

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
