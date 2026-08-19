# State system (deep)

## 1. Two effects, not five kinds of state

| Constructor | Effect | Storage |
|-------------|--------|--------|
| **MorphState** | Participates in dirty projection → may auto-morph | plane backend |
| **RefState** | Silent; excluded from dirty snapshot | instance `__dict__` only |

Historical names Session/Client/Store/Transient are **not** public APIs. Storage is a **parameter** (`backend=`), not a type hierarchy.

Sugar (all MorphState):

| Alias | Default backend |
|-------|-----------------|
| `UiState` | `session` |
| `PrefState` | `client` (expects `key=`) |
| `KeepState` | `store` |

## 2. Using multiple fields together

```python
class Panel(Component):
    id = "panel"
    page = MorphState("home")                      # session
    theme = MorphState("system", backend="client", key="ui.theme")
    draft = MorphState("", backend="store")
    nonce = RefState("")
```

| Action mutates | Auto-morph if `return None`? |
|----------------|------------------------------|
| `page` only | Yes |
| `theme` only | Yes (client Morph still dirty-tracked) |
| `draft` only | Yes |
| `nonce` only | **No** |
| `page` + `nonce` | Yes (page dirty) |

Dirty comparison uses `vars(inst)` public keys **minus** Ref field names. Values are compared by equality (`!=`).

## 3. Storage key layout

| Plane | Key |
|-------|-----|
| session | `{component.id}.{field_name}` |
| store | `{component.id}.{field_name}` |
| client | `key=` if provided, else `field_name` |
| ref | not in plane bags |

## 4. Plane backends lifecycle

```text
boot
  → MemoryPlanes for session, client, store (unlocked)
Host may:
  app.state.use("store", host_kv, lock=True)   # typical production
attach(Channel):
  if session unlocked → ChannelSessionBackend (source=channel, unlocked)
  if client unlocked  → ChannelClientBackend
  locked planes are never overwritten by attach
```

`app.state.report` → `{ "session": "memory"|"channel"|"host", ... }`.

Custom backends must implement:

```python
class PlaneBackend(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
```

`DictBackend` is the in-memory implementation (`data: dict`).

## 5. Descriptor read/write sequence

**Get**

1. If instance has bound Behavior and field has a plane backend path → `plane_get`.
2. Else instance `__dict__` / default.

**Set**

1. `type=` exact-class check (no coercion).
2. `validate=` callable may transform or raise.
3. If preview and plane in `{session, store}` → `AuthorityError`.
4. If plane `client` and `client_risk` → path policy.
5. `plane_set` if backend present; else error.
6. Mirror into `inst.__dict__[name]` for dirty snapshots.

## 6. SSR / dual process notes

- Memory planes are **process-local**. Multi-worker Hosts must `state.use` shared store/session adapters (Redis, etc.) or accept sticky sessions.
- Client plane under Channel is preference projection; Behavior also mirrors locally for offline reads.
- Morph HTML is produced by `render()` at dispatch time on the worker that handled the action — keep `render()` pure w.r.t. request-local data.

## 7. What not to store in Morph fields

| Avoid in Morph/Ref | Put instead |
|--------------------|-------------|
| Order lines, payments, balances | Host domain DB |
| Large blobs | Object storage + id in store plane |
| Secrets | Secret manager; Ref only for non-secret request correlation ids |

## 8. Interaction with return values

| Return | Dirty Morph | Result |
|--------|-------------|--------|
| `None` | yes | `refresh` → morph |
| `None` | no | `[]` |
| `list[Op]` | ignored for auto morph | Ops used as-is (must include any morph you need) |

If you return explicit Ops, **you** own refresh; dirty auto-morph does not also run.
