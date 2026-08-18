# Design — ux-behavior

**Status:** Binding for this parallel library  
**Date:** 2026-08-18

## 1. One-sentence contract

> Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.

## 2. Why this package exists

The stack needs exactly one place where product meaning is allowed to become Ops without importing Channel or CEK.

That seat was previously occupied by `ux-app`. This library reimplements the seat with:

- clearer name
- lower cognitive load
- progressive disclosure instead of dual audiences
- frozen public surface from day 1
- no historical residue

## 3. Name decision

| Candidate | Verdict |
|-----------|---------|
| ux-app | Current. Generic. |
| ux-author | Good role word, felt too generic to the user ("anyone writes") |
| ux-compose | Strong mechanism word, collides with the `compose` function |
| ux-host | Collides with CEK Host and product Host seat |
| ux-shell | Collides with Document shell and Host visual shell |
| **ux-behavior** | **Chosen.** Specific to what the developer is defining, low collision, good signal |

American spelling preferred for ecosystem consistency. British `behaviour` is an acceptable alias in prose.

## 4. Public surface rules

- Day-1 vocabulary is small and frozen.
- Chrome is expressed as verbs: `open`, `close`, `select`, `confirm`.
- `compose` / `lower` live only under `ux_behavior.wire`.
- Ports and session key schemes are internal.
- No second finish path (`reply`, effects catalogs, dual morph helpers).

## 5. Progressive disclosure

```text
Happy path          →  Behavior, Component, action, update/notify/go, open/close
Host / live Result  →  from ux_behavior.wire import compose, lower
```

Authors never see the wire door unless they need it. The door is intentional friction that protects isolation and the XOR law.

## 6. Hard laws (unchanged)

- Only the wire/door modules may import cores.
- Cold `import ux_behavior` loads no Channel / CEK.
- One Result: `morph(T)` XOR `scene.enter(T, html=...)`.
- No fifth kernel.
- One intent → one name.
- Markup stays in Document. Caps stay in Channel. Chrome/layout stay in Host.

## 7. Comparison with ux-app

See README table. Summary: same architectural laws, better naming, better framing, smaller surface, progressive instead of dual.

## 8. Reopen conditions

Changing the public surface, exporting wire helpers on top-level `__all__`, or inventing a second finish path requires a new entry in this file with explicit rationale.
