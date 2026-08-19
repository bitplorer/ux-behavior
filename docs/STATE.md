# Component field state

## Canonical pair

| API | Effect | Analogy |
|-----|--------|--------|
| **MorphState** | Change may auto-morph when action returns `None` | `useState` |
| **RefState** | Remember only; never auto-morph | `useRef` |

```python
page  = MorphState("home")                                  # session
theme = MorphState("system", backend="client", key="ui.theme")
step  = MorphState(1, backend="store")
n     = MorphState(0, type=int)                             # no coerce
token = RefState(None)
```

Sugar: `UiState` (session), `PrefState` (client), `KeepState` (store).

## Dirty projection

On `return None`, Behavior compares public instance state **excluding RefState fields**.
If Morph fields changed → `refresh(component.id)` → `ui.dom.morph`.

## Storage planes

| Plane | Typical use | Default backend |
|-------|-------------|-----------------|
| `session` | UI navigation, menus | memory |
| `client` | Theme/density prefs | memory (Channel if attached) |
| `store` | Durable draft / Host kv | memory |
| `ref` | Internal only (RefState) | instance `__dict__` |

Keys:

- session/store: `{component.id}.{field}`
- client: `key=` if set, else field name

### Host wiring

```python
app.state.use("store", my_backend)   # locks by default
app.state.report
```

Attach may set session/client to Channel backends only if **unlocked**.

### Client risk

Paths matching money-shaped names (`price`, `amount`, `qty`, …) refuse on client plane when `client_risk=True` (default).

## Write guards

| Param | Behavior |
|-------|----------|
| `type=int` | `type(value) is int` (via isinstance check after resolving annotations) |
| `validate=fn` | `value = fn(value)` may raise |

## Preview

```python
with app.preview():
    # session/store Morph writes → AuthorityError
    # client / Ref still writable
```
