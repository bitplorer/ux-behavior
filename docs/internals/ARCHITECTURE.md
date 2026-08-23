# Architecture

> **Diátaxis:** explanation · **Canonical:** `docs/internals/ARCHITECTURE.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## 1. Purpose

**ux-behavior** is the **standard product-behavior interface** for Host applications that may optionally attach to **ux-channel**.

It turns:

```text
Component state + @action methods + user/system triggers
```

into:

```text
list[Op]   # verified against an agreed stamp
```

with explicit policy for Caps, storage planes, validation, and diagnostics.

It is **not** a general web framework, not a Cap cryptosystem, and not a design system.

## 2. Layer diagram

```text
┌───────────────────────────────────────────────────────┐
│  Host product                                              │
│  layout, domain SQL, ASGI app, business rules              │
├───────────────────────────────────────────────────────┤
│  ux-behavior                                               │
│  Behavior, Component, @action, Morph/Ref, Ops, stamp,      │
│  Cap *policy*, diagnostics, wire *door*                    │
├───────────────────────────────────────────────────────┤
│  ux-channel (optional at runtime)                          │
│  Cap mint/verify, transport, Peer apply, client safety      │
├───────────────────────────────────────────────────────┤
│  ux-dom (optional)                                         │
│  markup trees, tokens                                      │
└───────────────────────────────────────────────────────┘
```

**Import law:** only `ux_behavior.wire.*` may import `ux_channel`. Author modules never do. Doctor enforces this.

## 3. Core objects

| Object | Responsibility | Not responsible for |
|--------|----------------|---------------------|
| **Behavior** | Registry, dispatch, stamp, planes policy, attach, diagnostics | Domain transactions, Cap HMAC |
| **Component** | Stable `id`, fields, `@action` methods, `render()` | Global routing, Cap mint |
| **@action** | Mark verb; normalize return; store `caps` | Auth crypto |
| **MorphState** | Durable-ish field that may trigger morph | Domain aggregate integrity |
| **RefState** | Silent memory | UI refresh |
| **Op** | Single stamped instruction | Applying to the DOM |
| **Continuation** | Deferred action bound to an event name | Payment provider webhooks |
| **Diagnostics** | Structured record of degrade/refuse | Metrics backend |

## 4. End-to-end data flow

```text
1. Host builds Behavior, adds Components, optional state.use / use(domains)
2. Optional: attach(asgi) → Channel region + dispatch handler + plane adapters
3. Browser/control path:
     control(action, **args)
       → offline attrs  OR  Channel.control(...).as_ux_dom() Cap bundle
4. Inbound event (live):
     Channel verifies Cap / session
       → wire handler
       → async_dispatch(name, _trusted=True, **payload)
5. Dispatch pipeline (see DISPATCH.md)
6. list[Op] returned to Channel/Host for apply (morph, log, nav, …)
```

Offline unit tests skip steps 2–4 and call `dispatch` directly.

## 5. Coupling rules (stable)

| Coupled | Decoupled |
|---------|-----------|
| Action methods live **on** Components | Actions are not free-floating RPCs |
| Behavior **runs** actions | Behavior does not own domain SQL |
| MorphState dirty → morph **that** component | RefState never alone |
| Cap **policy** in Behavior | Cap **crypto** in Channel |

## 6. Explicit non-goals

| Non-goal | Owner |
|----------|--------|
| Second Cap implementation | Forbidden |
| HTML component library | ux-dom |
| ORMs / cart line items as library types | Host |
| Motion timeline engine | optional Host / motion package |
| Multi-tenant auth product | Host + Channel |

## 7. Failure philosophy

1. **Prefer raise** for policy violations (Caps, stamp, preview, client risk).
2. **Prefer morph Ops** for user-input validation (field errors).
3. **Prefer diagnostics warn/error + hint** for degraded paths (offline control, plane fallback).
4. **Never** `except: pass` without a diagnostic event.

## 8. Versioning

- Public names in `ux_behavior.__all__` are **frozen** (doctor).
- Expanding `__all__` without updating isolation freeze is a CI failure.
- Wire APIs may evolve behind `ux_behavior.wire` without expanding top-level surface.
