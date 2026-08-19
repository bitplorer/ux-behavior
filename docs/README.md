# ux-behavior documentation

**Audience:** engineers shipping product UI behavior on Channel-backed (or offline-test) Hosts.

This is the **production** documentation set. Tutorials exist for onboarding; the pages below are the contract.

## Reading order

| Priority | Document | Purpose |
|----------|----------|--------|
| 1 | [ARCHITECTURE.md](ARCHITECTURE.md) | System boundaries, data flow, non-goals |
| 2 | [SECURITY.md](SECURITY.md) | Caps policy, trust, client risk, preview, secrets |
| 3 | [STATE_DEEP.md](STATE_DEEP.md) | Morph/Ref, planes, dirty projection, SSR, Host backends |
| 4 | [DISPATCH.md](DISPATCH.md) | Sync/async pipeline, validation, Ops, stamp |
| 5 | [WIRE.md](WIRE.md) | attach, control, planes, drivers, failure matrix |
| 6 | [API.md](API.md) | Exhaustive public API |
| 7 | [ERRORS.md](ERRORS.md) | Exception + diagnostic catalog with recovery |
| 8 | [OPERATIONS.md](OPERATIONS.md) | Boot profiles, observability, tests, doctor |
| 9 | [PRODUCTION_APP.md](PRODUCTION_APP.md) | Full multi-component system |
| 10 | [MIGRATION_UX_APP.md](MIGRATION_UX_APP.md) | Kill-path from ux-app |

### Onboarding (shallower)

[tutorial/README.md](tutorial/README.md) · [GUIDE.md](GUIDE.md)

### Package version

Docs target **ux-behavior 0.3.x**. Behavior that differs by minor version is called out explicitly.
