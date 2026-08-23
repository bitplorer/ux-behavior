# ux-behavior documentation index

**Start:** [../START_HERE.md](../START_HERE.md) · kept: [../START.md](../START.md)
**Binding design:** [../DESIGN.md](../DESIGN.md)
**Audience table also on:** [README.md](README.md)

This layer owns product behavior → verified `list[Op]`.
It does **not** own raw HTML construction or wire codecs.

## Folder contract (Phase 2)

| Folder | Diátaxis mode | May contain | Must not contain |
|--------|---------------|-------------|------------------|
| `docs/guides/` | how-to | Goal-oriented recipes | Conceptual essays as primary form |
| `docs/reference/` | reference | Facts, signatures, tables | Learning narrative as primary form |
| `docs/internals/` | explanation | Why, architecture, C4 | Step lists as primary form |
| `docs/examples/` | examples | Worked recipes / pointers | Law |
| `docs/adr/` | ADR | Decisions (or an index of them) | Mixed how-to |

Specialized folders (`security/`, `ship/`, `design/`, `tutorial/`, `patterns/`, `archive/`) stay.
`docs/INDEX.md` is the map. Do not add a second competing map.

---

## Audience

| You are… | Start (≤ 2 clicks from repo root) |
|----------|-----------------------------------|
| **New** | [../START_HERE.md](../START_HERE.md) |
| **Learning by building** | [tutorial/](tutorial/README.md) |
| **Shipping a widget** | [patterns/](patterns/README.md) |
| **Need API facts** | [reference/API.md](reference/API.md) · [reference/REFERENCE.md](reference/REFERENCE.md) |
| **Maintainer / agent** | [../DESIGN.md](../DESIGN.md) · [../AGENTS.md](../AGENTS.md) · [../CONTRIBUTING.md](../CONTRIBUTING.md) |

---

## By Diátaxis mode

### Tutorial

| Doc | Purpose |
|-----|---------|
| [../START_HERE.md](../START_HERE.md) | 5-minute path |
| [../START.md](../START.md) | Short start (kept) |
| [tutorial/](tutorial/README.md) | Progressive onboarding 01–10 |
| [guides/GUIDE.md](guides/GUIDE.md) | Narrative guide |

### How-to

| Doc | Purpose |
|-----|---------|
| [patterns/README.md](patterns/README.md) | Widget + complex index |
| [patterns/COMPLEX_NESTED.md](patterns/COMPLEX_NESTED.md) | Full product systems |
| [patterns/COMPLEX.md](patterns/COMPLEX.md) | Infinite scroll, optimistic UI, … |
| [patterns/MORE_CASES.md](patterns/MORE_CASES.md) | Residuals |
| [patterns/NESTED.md](patterns/NESTED.md) | Nesting rules |
| [patterns/](patterns/README.md) | accordion, carousel, confirm, drawer, dropdown, filters, forms, modal, nested_chrome, pagination, tabs, toasts, typeahead, wizard |
| [examples/EVERY_MODE.md](examples/EVERY_MODE.md) | Offline/online × Caps × async |
| [examples/EXAMPLES_MATRIX.md](examples/EXAMPLES_MATRIX.md) | Per-family matrix |
| [examples/OFFLINE_ONLINE.md](examples/OFFLINE_ONLINE.md) | Test parity |
| [examples/MATRIX_ALL.md](examples/MATRIX_ALL.md) | Full pattern Caps map |
| [examples/EXAMPLES.md](examples/EXAMPLES.md) | Examples index |
| [guides/OPERATIONS.md](guides/OPERATIONS.md) | Operations |
| [guides/PRODUCTION_APP.md](guides/PRODUCTION_APP.md) | Production app notes |
| [../MIGRATION.md](../MIGRATION.md) | Migration from ux-app |
| [guides/MIGRATION_UX_APP.md](guides/MIGRATION_UX_APP.md) | Docs-side migration notes |
| [../LIVE_CHECKS.md](../LIVE_CHECKS.md) | Live checks |

### Reference

| Doc | Purpose |
|-----|---------|
| [reference/API.md](reference/API.md) | Surface reference |
| [reference/REFERENCE.md](reference/REFERENCE.md) | Broader reference |
| [reference/DISPATCH.md](reference/DISPATCH.md) | Dispatch |
| [reference/ERRORS.md](reference/ERRORS.md) | Errors |
| [reference/STATE.md](reference/STATE.md) | State API |
| [reference/STATE_DEEP.md](reference/STATE_DEEP.md) | State (deep) |
| [reference/STATE_PLANES.md](reference/STATE_PLANES.md) | Redirect → STATE.md |
| [reference/WIRE.md](reference/WIRE.md) | Wire door |
| [reference/SECURITY.md](reference/SECURITY.md) | Security |
| [reference/BEHAVIOR.md](reference/BEHAVIOR.md) | Behavior notes |
| [reference/CONTROL_FLOW.md](reference/CONTROL_FLOW.md) | Control flow |
| [reference/HOST.md](reference/HOST.md) | Host attach |
| [../CHANGELOG.md](../CHANGELOG.md) | History (not current teaching) |

### Explanation

| Doc | Purpose |
|-----|---------|
| [../DESIGN.md](../DESIGN.md) | Binding design (one decision set) |
| [adr/README.md](adr/README.md) | ADR slot → DESIGN.md |
| [internals/c4.md](internals/c4.md) | C4-style context |
| [internals/ARCHITECTURE.md](internals/ARCHITECTURE.md) | System design |
| [internals/INTERNALS.md](internals/INTERNALS.md) | Internals |
| [../KILL_UX_APP.md](../KILL_UX_APP.md) | Why ux-app was retired (history; not current API) |

---

## Sister layers

| Package | Role |
|---------|------|
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Presence / transition plans |
| [ux-compose](https://github.com/bitplorer/ux-compose) | Composition + product CLI |

Do not flatten these layers into this repo.

