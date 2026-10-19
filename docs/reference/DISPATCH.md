# Dispatch pipeline

> **Diátaxis:** reference · **Canonical:** `docs/reference/DISPATCH.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## 1. Entry points

| Method | Async actions | Sync actions |
|--------|---------------|--------------|
| `dispatch` | **TypeError** | yes |
| `async_dispatch` | yes | yes |
| `submit` / `async_submit` | same as above | merges `args` dict |
| `emit` / `async_emit` | via dispatch family | resolves continuation first |

Reserved kwargs: `_trusted`. Only the module-private sentinel grants trust, and only the wire passes it, after Channel has accepted the Cap. `True`, `"yes"`, `1`, and any other value are ignored and logged. A `_trusted` entry in `submit` / `async_submit` args, a Channel form or args payload, continuation slots, or `dispatch(action, **body)` is posted data and does not grant trust. The key is stripped before binding. Hosts use `app.trust()` for tests and admin paths.

## 2. Pipeline (ordered)

```text
1. Parse "component.method"
2. Lookup component; get attribute
3. Require _ux_behavior_action marker
4. Sync path: reject _ux_behavior_async
5. Cap policy (_require_caps)
6. bind_action_args (product signature of the @action function, not
      BoundAction.__call__(*args); Channel ``args=dict`` unpacks unless the
      action declares ``args``; VAR_POSITIONAL/VAR_KEYWORD are not kwargs)
      on ValidationError → return error morph Ops (no raise)
7. Open follow_up contextvar bucket
8. Snapshot public state (exclude Ref names)
9. Call action (await if async)
10. Close bucket; register Continuations on Behavior
11. If result is None:
      compare snapshot → refresh if dirty
    elif list[Op]:
      use list
    else:
      TypeError
12. Stamp-check every Op
13. Return list[Op]
```

## 3. Validation behavior

Uses `inspect.signature` and resolves each parameter annotation on its own (including `from __future__ import annotations`).

- Missing required params → field error.
- Simple type mismatch → field error.
- Union/Optional: None allowed when present in union; other branches lightly checked.
- Complex generics: treated as pass-through (not a full type checker). `list[int]` does not check its elements.
- An annotation that cannot be resolved is skipped for that parameter only. It does not turn off checks on the other parameters.

Error morph target: `{action}.{field}-error` or `{action}-error` for `_`.

## 4. Continuations

```python
follow_up(event, action, *, args_from=None, **args)
```

- Must run inside step 7–9 context; otherwise `RuntimeError`.
- Overwrites prior continuation for the same `event` name on this Behavior in the same `contextvars` context. Callers that share a context overwrite each other. A copied context keeps its own armed event.
- `emit` merges: fixed `args`, then `args_from` mapping from slots, then extra slots. A source key that was copied onto its destination is consumed and is not forwarded. Slots that were not consumed are still forwarded.
- Continuation dispatch inherits the trust of the dispatch that armed it (0.4.0). A follow-up armed by an anonymous public action is checked like any untrusted call. A trusted host (e.g. a verified payment webhook) emits inside `app.trust()` or arms from a dispatch the wire already marked trusted.

## 5. Stamp

Default pairs always include baseline UI/nav/kv/log. `app.use("effects")` / `app.use("search")` / `app.domain(...)` extend the set.

Undeclared `(ns, name)` → `PermissionError` + `STAMP_REJECT`.

## 6. Concurrency

- One Behavior instance is **not** claimed thread-safe for concurrent dispatch on shared Component state.
- ASGI: one request → one dispatch await; avoid sharing mutable Component instances across in-flight requests without external locking.
- Armed continuations are per Behavior and per `contextvars` context. The scope key is weak, so a collected Behavior does not leave its args in a long-lived context. On the next read or arm in a context, each `args` and `args_from` value is `copy.deepcopy`'d. A value whose deepcopy raises stays shared with the source. `contextvars.copy_context()` does not fork the bag: a `Continuation` object held across that call is shared, so treat `args` as immutable. Same-context callers still overwrite the same event name. Identity is not stored on Behavior.
