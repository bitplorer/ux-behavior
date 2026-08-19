# Kill ux-app — ownership map

**Goal:** Hosts (harbor) run on **ux-behavior + ux-channel + ux-dom** only.
ux-app is no longer required.

## Feature → owner

| ux-app feature | Owner after kill |
|----------------|------------------|
| `App` / composition root | **ux-behavior** `Behavior` |
| `Component` + `@action` | **ux-behavior** |
| `update` / `notify` / `go` | **ux-behavior** |
| `open_overlay` / `close` / `select` / `confirm` | **ux-behavior** `open`/`close`/`select`/`confirm` |
| `form_result` | **ux-behavior** `submit_outcome` |
| `Session` / `Client` / `Store` / `Transient` | **ux-behavior** field markers (local bag; live mirror optional later) |
| Domain stamp / `use` | **ux-behavior** |
| Peer drivers | **Channel / Host** |
| Cap mint / verify / once-store | **ux-channel** (via wire `control`) |
| `control` attrs for HTMX | **ux-behavior** `Behavior.control` → Channel when attached |
| `submit` / dispatch | **ux-behavior** `dispatch` / `submit` |
| `compose` / `lower_morph` / Result XOR | **ux-behavior.wire** |
| Channel ASGI attach | **ux-behavior.wire.attach** |
| Region paint | Host callback + Channel Region |
| Document / markup / Badge / Dialog | **ux-dom** |
| Page shell / layout / script tags | **Host** |
| `finish()` notice + menu close | **Host** (harbor `wiring.finish`) |
| `act` / `wire` HTMX helpers | **Host** |
| Production receipts / CEK hard mode | **Channel + CEK** |
| UI composite health | **ux-dom** / Host |
| Preview / follow_up | Host or drop |

## Must remain out of ux-behavior

- Product chrome markup (topbar, toast TTL, brand)
- HTML page assembly
- Direct `import ux_channel` from product modules
- Fifth package / glue layer

## Harbor cutover checklist

1. `from ux_behavior import Behavior, Component, action, Session, …`
2. Replace `App.boot` → `Behavior.boot` + `attach(asgi)`
3. Replace overlay helpers with chrome verbs
4. Move `finish` / `act` / `wire` into Host (already in `app/wiring.py`)
5. Caps: `host.control(fn, **args)` after attach
6. Remove ux-app dependency from `pyproject.toml`
7. Run pilot + live tests green

## Status

Author seat + field markers + control door implemented in ux-behavior.
Host-owned helpers stay in harbor.
