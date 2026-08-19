# Public API (exhaustive)

Top-level exports are exactly `ux_behavior.__all__` (doctor-frozen).

## Behavior.boot

```python
@classmethod
def boot(
    cls,
    title: str = "",
    *,
    strict_caps: bool = True,
    client_risk: bool = True,
    strict_control: bool = False,
    strict_attach: bool = False,
) -> Behavior
```

## Behavior instance methods

| Method | Signature (conceptual) | Returns |
|--------|------------------------|--------|
| `add` | `(type\|instance) -> instance` | component |
| `get` | `(id: str) -> instance` | raises KeyError with hint |
| `components` | `() -> dict` | copy |
| `actions` | `(id=None) -> list[str]` | sorted names |
| `dispatch` | `(action: str, **kwargs) -> list[Op]` | |
| `async_dispatch` | `async (action, **kwargs) -> list[Op]` | |
| `submit` | `(action, args=None, **kw) -> list[Op]` | |
| `async_submit` | async variant | |
| `emit` | `(event, **slots) -> list[Op]` | |
| `async_emit` | async variant | |
| `control` | `(action, **args) -> dict[str,str]` | |
| `refresh` | `(id) -> list[Op]` | single morph |
| `attach` | `(asgi, **kw) -> Channel\|None` | |
| `region` | `(render, *, uid=None) -> self` | chain |
| `use` | `(*domain_names) -> self` | chain |
| `domain` | `(name, version, pairs) -> self` | chain |
| `preview` | context manager | |
| `trust` | context manager | |

### Properties

`title`, `strict_*`, `client_risk`, `diagnostics`, `state`, `stamp`, `continuations`, `cores_available`, `is_preview`

## @action

```python
def action(fn=None, *, caps: tuple[str, ...] | list[str] = ())
```

Sets `_ux_behavior_action`, `_ux_behavior_caps`, `_ux_behavior_async`.

## Fields

```python
MorphState(
    default: Any = None,
    *,
    backend: str | PlaneBackend = "session",
    key: str | None = None,
    type: type | None = None,
    validate: Callable[[Any], Any] | None = None,
)
RefState(default=None, *, type=None, validate=None)
```

## Ops

`Op(ns, name, payload)` frozen. Helpers: `update`, `notify`, `go`, `submit_outcome`, `open`, `close`, `select`, `confirm`.

## follow_up

```python
follow_up(event: str, action: str, *, args_from: dict[str,str] | None = None, **args) -> Continuation
```

## Errors

`BehaviorError(message, *, hint="")`, `AuthorityError`, `ContinuationError`, `ValidationError` (`.fields`).

## StateAPI

`use`, `reset`, `report`, `locked`, `backends`, `backend`, `is_locked`.

## DictBackend

In-memory `{key: value}` with `get`/`set`.
