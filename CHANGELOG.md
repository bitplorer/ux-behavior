# Changelog

## Unreleased

### Wire

- `ux_behavior.wire.client_event` — Host-only Channel `{op: "dispatch"}` helper for CustomEvent. Not on the frozen public surface.

## 0.3.2

### Restore

- Full `Behavior` composition root (`src/ux_behavior/root.py`) restored after a truncated write in 0.3.1.

### Polish

- Diagnostics `HINTS` restored for every attach / control / plane code still emitted (dropped during the truncated 0.3.1 pass).
- `developer_hints=False` (default): Cap 403 text and diagnostic hints never include `trust()` / `_trusted` recipes.
- `strict_attach=True` fails closed when `ux-channel` is missing, not only on `Channel.boot` failure.
- LICENSE (MIT) and `.gitignore`.
- START.md and API.md aligned with MorphState / `developer_hints`.

## 0.3.1

### Polish

- README rewritten as the single entry point (mental model, docs map, install, tests).
- Optional extra: `pip install "ux-behavior[channel]"`.
- CLI `new action` stub uses a clear docstring (no TODO noise).
- Documentation index aligned with patterns, mode matrix, offline/online parity.
- Package metadata: Documentation URL, pytest warning filter.

### Tests (cumulative)

- Offline examples matrix, online HTTP matrix, parity extras, every-mode sync/async × Caps.

## 0.3.0

- Follow-up / emit continuations.
- Caps posture + strict offline defaults.
- Dual sync/async dispatch, submit, emit.
- Diagnostics with actionable hints.
- MorphState / RefState + plane backends.
- Chrome Ops, validation morphs, client-risk guards.
