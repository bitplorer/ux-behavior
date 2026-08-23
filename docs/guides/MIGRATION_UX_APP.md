# Migration from ux-app

> **Diátaxis:** how-to · **Canonical:** `docs/guides/MIGRATION_UX_APP.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

## Mapping

| ux-app | ux-behavior |
|--------|-------------|
| `App` | `Behavior` |
| `Component` | `Component` |
| `@action` | `@action` |
| `Session`/`Client`/`Store`/`Transient`/`Sealed` | `MorphState(backend=…)` / `RefState` / `type=` |
| `form_result` | `submit_outcome` |
| `open_overlay` … | `open` / `close` / `select` / `confirm` |
| `follow_up` | `follow_up` + `emit` |
| Cap machine | Channel only |
| `set_plane_backend` | `app.state.use` |

## Do not port

Badge/html helpers → ux-dom. Peer/LocalRuntime → Channel. Domain tables → Host.

## Residual Host work

1. Install Channel for live Caps.  
2. Replace plane aliases with Morph/Ref.  
3. Point buttons at `app.control`.  
4. Run doctor.  
