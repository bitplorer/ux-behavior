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

Reserved kwargs: `_trusted` (bool) — stripped before binding to the action signature.

## 2. Pipeline (ordered)

```text
1. Parse "component.method"
2. Lookup component; get attribute
3. Require _ux_behavior_action marker
4. Sync path: reject _ux_behavior_async
5. Cap policy (_require_caps)
6. bind_action_args (signature + annotations)
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

Uses `inspect.signature` + `typing.get_type_hints` (resolves `from __future__ import annotations`).

- Missing required params → field error.
- Simple type mismatch → field error.
- Union/Optional: None allowed when present in union; other branches lightly checked.
- Complex generics: treated as pass-through (not a full type checker).

Error morph target: `{action}.{field}-error` or `{action}-error` for `_`.

## 4. Continuations

```python
follow_up(event, action, *, args_from=None, **args)
```

- Must run inside step 7–9 context; otherwise `RuntimeError`.
- Overwrites prior continuation for the same `event` name on this Behavior.
- `emit` merges: fixed `args`, then `args_from` mapping from slots, then extra slots.
- Continuation dispatch uses `_trusted=True` (armed under an already authorized action). Hosts that expose raw `emit` on the network must still authenticate the caller.

## 5. Stamp

Default pairs always include baseline UI/nav/kv/log. `app.use("effects")` / `app.use("search")` / `app.domain(...)` extend the set.

Undeclared `(ns, name)` → `PermissionError` + `STAMP_REJECT`.

## 6. Concurrency

- One Behavior instance is **not** claimed thread-safe for concurrent dispatch on shared Component state.
- ASGI: one request → one dispatch await; avoid sharing mutable Component instances across in-flight requests without external locking.
- Continuations dict is per Behavior instance.
