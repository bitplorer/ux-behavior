# DESIGN — ux-behavior

**Status:** Binding  
**Audience:** Staff+ engineers, architecture review, board-level technical discussion  
**Date:** 2026-08-18  
**Version:** 0.3.2 (foundation freeze 0.1; MorphState/RefState joined Day-1)

---

## 0. One-sentence contract

> **Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.**

If a change cannot be explained under this sentence, it does not belong in this library.

---

## 1. Why this library exists

The ux stack needs exactly **one** place where product meaning is allowed to become Ops without importing Channel or CEK.

That seat was previously occupied by `ux-app`. `ux-app` got the architecture right and the framing wrong:

| What ux-app got right | What made it feel heavy |
|-----------------------|-------------------------|
| Isolation law (only the door imports cores) | Generic name `App` / `ux-app` |
| Cold import clean | Dual-audience framing without progressive disclosure |
| XOR law on one Result | Adapter felt bolted-on |
| `update` / `notify` / `go` vocabulary | Historical residue and broader surface than needed |
| Component + Action model | Intermediate position poorly named |
| Caps required, doctor concept | Ports and internal schemes leaked into mental model |
| No fifth kernel | Cognitive load of “where do I put this?” |

`ux-behavior` keeps every hard law and redesigns the surface, naming, and progressive disclosure so the same power has lower cognitive load.

---

## 2. Position in the stack (cherry on top of ux-channel)

```text
CEK plane     cek-framework → cek-runtime → cek-host → cek-surface
UX peers      ux-dom  ⊥  ux-channel  ⊥  ux-motion
Behavior      ux-behavior     ← this library (author of product meaning)
Host          harbor / VEIN / any product (chrome, layout, brand)
```

- **Not a kernel.** There are still exactly two L1 kernels: Host (decide) and Peer (apply).
- **Not Document.** Markup and tokens stay in ux-dom.
- **Not Channel.** Wire, Caps, Peer apply stay in ux-channel.
- **Not Host.** Product chrome, `#view`, toast TTL, brand stay in the Host under the 3-host rule.

This library is the **only legal author of product behavior** that becomes Ops. It sits cleanly on top of Channel without becoming a second Channel or a second design system.

---

## 3. Name decision (closed)

| Candidate | Verdict |
|-----------|---------|
| ux-app | Current. Generic. Overloaded. |
| ux-author | Role-correct, too generic in everyday language. |
| ux-compose | Mechanism-correct, collides with `compose()`. |
| ux-host | Collides with CEK Host and product Host seat. |
| ux-shell | Collides with Document shell and Host visual shell. |
| **ux-behavior** | **Chosen.** Names what the developer is defining: product behavior. Low collision. High signal. |

American spelling for ecosystem consistency. British “behaviour” is acceptable in prose only.

---

## 4. Design principles (S-tier)

Derived from progressive disclosure practice (SwiftUI), API simplicity/composability/predictability (Stripe), explicit anti-patterns, and the verified stack laws.

1. **One primary mental model**  
   Product behavior → verified list[Op]. Everything else is progressive.

2. **Progressive disclosure**  
   Complexity of the call site grows with the complexity of the use case. Day-1 never sees the wire door.

3. **Small frozen public surface**  
   Every public name is intentional. No historical residue. No second finish path.

4. **Composable building blocks**  
   `update` / `notify` / `go` / chrome verbs / `compose` fit together predictably. No enumerating every possibility.

5. **Fail closed**  
   Empty targets, unknown items, XOR clashes, undeclared pairs, Cap violations → refuse. Never silent partial success.

6. **Isolation as a product feature**  
   Cold `import ux_behavior` loads no Channel/CEK. Application modules never import cores. Doctor fails the build if they do.

7. **Predictable outcomes**  
   Same inputs under the same Cap and stamp produce the same Ops. Navigate ordered last. Morph uses idiomorph strategy at the wire door.

8. **Explicit anti-patterns**  
   Named and banned: `reply`, dual finish APIs, Host-local glue.js, teaching Channel `transition.*`, fifth package, exporting wire helpers on top-level `__all__` without a reopen entry.

---

## 5. Public surface (frozen from v0.1)

### Day-1 (what 95% of product code imports)

```python
from ux_behavior import (
    Behavior,       # composition root
    Component,      # unit of behavior + render
    MorphState,     # dirty / must-repaint field
    RefState,       # silent field
    action,         # decorator; Caps required unless caps=()
    update,         # morph
    notify,         # S-only notice
    go,             # navigate (ordered last at compose)
    open, close, select, confirm,  # chrome verbs
    Op,             # advanced construction only
)
```

### Progressive door (Host / live Result / motion on same Result)

```python
from ux_behavior.wire import compose, lower, Conflict, Result
```

These are **not** on top-level `__all__`. The friction is intentional and documented as progressive disclosure, not as a second API.

### Explicitly not public

- Ports and session key schemes
- Internal adapters
- Any synonym for Glue / Bridge / Adapter / Contribution
- A second finish API (`reply`, effects catalogs, dual morph helpers)

---

## 6. Laws (unchanged from the verified stack)

| Law | Statement |
|-----|-----------|
| Isolation | Only modules under the wire/door may import `ux_channel` or `cek_*`. |
| Cold import | `import ux_behavior` loads no Channel, CEK, or wire codecs. |
| XOR | On one Result: `morph(T)` XOR `scene.enter(T, html=…)`. Enforced at compose time. |
| No fifth kernel | Two L1 kernels only (Host decide, Peer apply). LocalRuntime is in-process, not a third kernel. |
| One intent → one name | No synonyms for Glue, Bridge, Adapter, Contribution, or the chrome verbs. |
| Ownership | Markup → Document. Caps/wire → Channel. Chrome/layout → Host. Behavior → this library. |
| Caps | `@action(..., caps=[...])`. `caps=()` is the explicit public opt-out. Present Cap always verifies. |
| Pair identity | Op is `(ns, name)` with `name` one token. Undeclared pairs never leave the session stamp. |
| Two clocks | Authority (Action → Ops under Cap) vs Preview (Peer-local, never authority kv). |

---

## 7. Elevated capabilities (more powerful than the intermediate framing of ux-app)

1. **Result construction elevated**  
   Hosts prefer high-level helpers that already obey XOR and idiomorph. Low-level `lower` / `compose` remain available under the progressive door.

2. **Chrome as verbs**  
   `open` / `close` / `select` / `confirm` are first-class. Ports stay internal. One overlay cell by default.

3. **Doctor as a product feature**  
   Mechanical isolation scan + public surface freeze check + XOR tests. Fail closed in CI.

4. **Stability contract from day 1**  
   Public `__all__` is a freeze list. Expanding it, exporting wire helpers at top level, or inventing a second finish path requires a new DESIGN entry with reopen rationale.

5. **Clear attach order and runtime story**  
   Same correct attach order as the stack (Peer kernel then preview). LocalRuntime for tests when cores are absent.

---

## 8. Anti-patterns (named so they stay dead)

| Anti-pattern | Why it dies |
|--------------|-------------|
| Export `compose` / `lower` on top-level `__all__` | Destroys progressive disclosure; dual vocabulary |
| Host-local `glue.js` or second compositor | Taken name; one intent two names |
| Teach Channel `transition.*` | Pollutes immortal op table; Motion must stay droppable |
| Fifth package (`ux-kit`, `ux-paint`, …) | Third owner; version skew |
| `reply(*effects)` or dual finish API | Banned; authors finish one way |
| Import Channel from application modules | Isolation law |
| Promote Host chrome into the library without 3 independent Hosts | Absorbs one product’s habits |
| Merge visual `id=` with trust `data-channel-id` | Cap / morph collision |

---

## 9. Reopen conditions

A future change is legal only if it still satisfies the one-sentence contract **and** one of the following fires. Otherwise write a new DESIGN entry first.

| You want to… | Legal when |
|--------------|------------|
| Export wire helpers on top-level `__all__` | Evidence that day-1 authors need the wire more often than `update`/`notify`/`go` |
| Add a public name | It does not create a synonym and has a clear seat |
| Promote Host chrome into the library | 3+ independent Hosts share the exact policy |
| Teach Channel about motion | Never under this contract |
| Mint a fifth package | Never under this contract |

---

## 10. Success criteria (boardroom test)

A staff engineer from an S-tier company should be able to answer yes to all of the following after reading this file and the README:

1. What is the single job of this library?
2. What may application code never import?
3. Where does chrome live, and why?
4. How do I compose morph + motion without remounting images?
5. What is banned, and why is it banned?
6. How does complexity grow with use case (progressive disclosure)?

If any answer is ambiguous, the design is not done.

---

**End of binding design.**  
Superseding this file requires a new dated entry that cites a reopen condition and answers the six success criteria.
