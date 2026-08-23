# ux-behavior documentation index

**Start:** [../START_HERE.md](../START_HERE.md) · kept: [../START.md](../START.md)
**Binding design:** [../DESIGN.md](../DESIGN.md)
**Audience table also on:** [README.md](README.md)

This layer owns product behavior → verified `list[Op]`.
It does **not** own raw HTML construction or wire codecs.

---

## Audience

| You are… | Start (≤ 2 clicks from repo root) |
|----------|-----------------------------------|
| **New** | [../START_HERE.md](../START_HERE.md) |
| **Learning by building** | [tutorial/](tutorial/README.md) |
| **Shipping a widget** | [patterns/](patterns/README.md) |
| **Need API facts** | [API.md](API.md) · [REFERENCE.md](REFERENCE.md) |
| **Maintainer / agent** | [../DESIGN.md](../DESIGN.md) · [../AGENTS.md](../AGENTS.md) · [../CONTRIBUTING.md](../CONTRIBUTING.md) |

---

## By Diátaxis mode

### Tutorial

| Doc | Purpose |
|-----|---------|
| [../START_HERE.md](../START_HERE.md) | 5-minute path |
| [../START.md](../START.md) | Short start (kept) |
| [tutorial/](tutorial/README.md) | Progressive onboarding 01–10 |
| [GUIDE.md](GUIDE.md) | Narrative guide |

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
| [EXAMPLES.md](EXAMPLES.md) | Examples index |
| [OPERATIONS.md](OPERATIONS.md) | Operations |
| [PRODUCTION_APP.md](PRODUCTION_APP.md) | Production app notes |
| [../MIGRATION.md](../MIGRATION.md) | Migration from ux-app |
| [MIGRATION_UX_APP.md](MIGRATION_UX_APP.md) | Docs-side migration notes |
| [../LIVE_CHECKS.md](../LIVE_CHECKS.md) | Live checks |

### Reference

| Doc | Purpose |
|-----|---------|
| [API.md](API.md) | Surface reference |
| [REFERENCE.md](REFERENCE.md) | Broader reference |
| [DISPATCH.md](DISPATCH.md) | Dispatch |
| [ERRORS.md](ERRORS.md) | Errors |
| [STATE.md](STATE.md) | State API |
| [STATE_DEEP.md](STATE_DEEP.md) | State (deep) |
| [STATE_PLANES.md](STATE_PLANES.md) | Redirect → STATE.md |
| [WIRE.md](WIRE.md) | Wire door |
| [SECURITY.md](SECURITY.md) | Security |
| [BEHAVIOR.md](BEHAVIOR.md) | Behavior notes |
| [CONTROL_FLOW.md](CONTROL_FLOW.md) | Control flow |
| [HOST.md](HOST.md) | Host attach |
| [../CHANGELOG.md](../CHANGELOG.md) | History (not current teaching) |

### Explanation

| Doc | Purpose |
|-----|---------|
| [../DESIGN.md](../DESIGN.md) | Binding design (one decision set) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [INTERNALS.md](INTERNALS.md) | Internals |
| [../KILL_UX_APP.md](../KILL_UX_APP.md) | Why ux-app was retired (history; not current API) |

---

## Sister layers

| Package | Role |
|---------|------|
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Presence / transition plans |
| [ux-compose](https://github.com/bitplorer/ux-compose) | Composition + product CLI |
