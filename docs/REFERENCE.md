# API reference (public)

Import from `ux_behavior` unless noted. Surface is frozen by doctor (`isolation.FROZEN_PUBLIC`).

## Behavior

```python
Behavior.boot(
    title="",
    *,
    strict_caps=True,      # protected actions need Cap/trust offline
    client_risk=True,      # refuse money-shaped client paths
    strict_control=False,  # raise if Cap mint fails
    strict_attach=False,   # raise if Channel.boot fails
) -> Behavior
```

| Member | Role |
|--------|------|
| `add(Component\|instance)` | Register unit; binds `_behavior` |
| `get(id)` / `components()` | Lookup |
| `actions(id=None)` | List `component.method` names |
| `dispatch(name, **kwargs)` | Sync action |
| `async_dispatch(name, **kwargs)` | Sync or async action |
| `submit` / `async_submit` | Same with `args={}` merge |
| `emit` / `async_emit` | Fire continuation |
| `control(action, **args)` | Button attrs (Cap when live) |
| `refresh(id)` | Force morph from `render()` |
| `attach(asgi, **kwargs)` | Wire Channel; may return `None` |
| `region(render, uid=...)` | Root paint for attach |
| `use(*domain_names)` | Agree stamp packs |
| `domain(name, version, pairs)` | Custom pack + use |
| `state` | `StateAPI` storage policy |
| `diagnostics` | Structured events + hints |
| `preview()` | Context: block session/store writes |
| `trust()` | Context: disable strict_caps |
| `stamp` | `frozenset[(ns, name)]` |
| `continuations` | Armed follow-ups |
| `cores_available` | `{ux_dom, ux_channel: bool}` |

### dispatch kwargs reserved

- `_trusted=True` — skip offline Cap check (tests / wire after Channel auth)

## Component

```python
class Cart(Component):
    id = "cart"           # required stable string for addressing
    # fields...
    def render(self) -> Any: ...
    @action(caps=())
    def add(self, ...): ...
```

Thin base: holds `id`, optional `bind_behavior`, no plane magic in `__getattribute__`.

## @action

```python
@action(caps=())                    # public
@action(caps=("orders.write",))     # protected offline
@action                             # same as caps=() only if decorator used as @action with default — prefer explicit caps=()
```

Supports sync and async methods. Return `None | Op | list[Op]`.

## Ops macros

| Fn | Pair | Notes |
|----|------|-------|
| `update(target, html)` | `ui.dom.morph` | Author morph |
| `notify(message, level="info")` | `log.append` | Notice |
| `go(href)` | `nav.push` | Navigate |
| `submit_outcome(target, html, message=...)` | morph + optional notify | Form/submit result |
| `open` / `close` / `select` / `confirm` | chrome pairs | Product chrome verbs |

`Op` is a frozen dataclass: `ns`, `name`, `payload`, `.pair`, `.fq`.

## Fields

| Constructor | Effect |
|-------------|--------|
| `MorphState(default, backend="session"\|"client"\|"store"\|PlaneBackend, key=None, type=None, validate=None)` | May auto-morph (`useState`) |
| `RefState(default, type=None, validate=None)` | Never auto-morph (`useRef`) |
| `UiState` | Morph + session |
| `PrefState` | Morph + client (+ `key`) |
| `KeepState` | Morph + store |

- `type=` — exact class, no coerce  
- `validate=` — callable `(value) -> value`  
- Do not use Cap `seal=` language on fields  

## StateAPI (`app.state`)

```python
app.state.use("session"|"client"|"store", backend, *, lock=True, source="host")
app.state.reset(plane=None)
app.state.report     # {plane: "memory"|"host"|"channel"|...}
app.state.locked
app.state.backends
app.state.backend(plane)
```

`lock=True` (default) prevents attach from overwriting that plane.

## Continuations

```python
follow_up(event, action, *, args_from=None, **args) -> Continuation
app.emit(event, **slots)
await app.async_emit(event, **slots)
```

- `args` fixed at follow_up time  
- `args_from` maps `{action_param: emit_slot}`  

## Errors

| Type | When |
|------|------|
| `BehaviorError` | Base; `.hint` next step |
| `AuthorityError` | Cap / preview / client risk / plane |
| `ContinuationError` | emit without follow_up |
| `ValidationError` | bad args; `.fields`; dispatch returns morphs instead of raise |

## Wire (not top-level public noise)

```python
from ux_behavior.wire.attach import attach, attach_info, probe
from ux_behavior.wire import Result  # progressive Result builder if present
```

Prefer `app.attach` / `app.control`.
