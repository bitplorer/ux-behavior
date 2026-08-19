# Internals

## Package layout

```text
src/ux_behavior/
  root.py          Behavior composition root
  component.py     thin Component
  action.py        @action sync/async + normalize returns
  fields.py        MorphState / RefState descriptors
  state_api.py     app.state Host storage API
  planes.py        MemoryPlanes / DictBackend / MISSING
  ops.py / chrome.py   Op macros
  events.py        follow_up + Continuation (contextvar)
  domains.py       stamp packs
  validate.py      bind + type hints
  client_risk.py   client path policy
  diagnostics.py   structured events + HINTS
  errors.py        BehaviorError hierarchy
  isolation.py     doctor + frozen public surface
  wire/            ONLY place that may import ux_channel
    attach.py
    control.py
    channel_planes.py
    drivers.py
    …
```

## Isolation law

- Non-`wire/` modules must not import `ux_channel` or `cek_*`.
- Doctor scans imports and banned tokens.
- Public `__all__` must match `FROZEN_PUBLIC`.

## Descriptor read/write

```text
MorphState.__get__
  → behavior.plane_get(plane, inst, field) if bound
  → else inst.__dict__ / default

MorphState.__set__
  → type/validate guards
  → plane_set (preview + client_risk)
  → mirror into inst.__dict__

RefState
  → only inst.__dict__ (plane "ref")
```

## Dispatch pipeline

```text
1 resolve component.method
2 reject async on sync dispatch
3 Cap policy
4 bind_action_args (ValidationError → morphs)
5 begin follow_up context
6 call action
7 collect continuations
8 None + dirty Morph → refresh; else use returned Ops
9 stamp check each Op
```

## Why soft Channel

Author/tests run without Channel. Production Hosts attach once. Cap crypto stays one implementation (Channel).
