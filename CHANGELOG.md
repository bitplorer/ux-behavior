# Changelog

## Unreleased

### Breaking

- `_trusted=True` no longer grants trust. A payload `_trusted` value is
  dropped, and the trust argument accepts only the private sentinel.
  `dispatch(action, **body)` does not grant trust. After a Cap check, call
  `dispatch_verified(name, payload)` or `async_dispatch_verified(name, payload)`.
  `app.trust()` is unchanged, and a task started inside it keeps trust for
  its whole life.
- `attach()` requires `UX_CHANNEL_SECRET` or `UX_BEHAVIOR_SECRET` outside
  dev. The published dev constant is refused even when passed explicitly.

### Added

- `dispatch_verified(name, payload)` and `async_dispatch_verified(name, payload)`
  grant trust for that one call after a Cap check. A task started inside the
  action does not inherit the grant. The private sentinel stays off the
  public surface.

### Security

- `attach()` no longer signs Caps with the published constant
  `dev-secret-key-32chars-minimum!!!!`. Outside dev that call raises
  (`ATTACH_SECRET_REQUIRED`) when no secret is configured. Dev is `DEBUG`
  in `1` / `true` / `yes` / `on` after strip + lower; this package has no
  other dev switch. In dev, a missing secret is one random per-process
  value with the same shape as `ChannelConfig.development()`. The constant
  is refused in every mode, including `UX_CHANNEL_SECRET` /
  `UX_BEHAVIOR_SECRET` and `ChannelConfig.production` when `REDIS_URL` is
  set. Reason: a Cap signed with that constant was accepted on a stock
  `attach()` that had no secret.
- `attach()` raises without a secret outside dev, so `UX_CHANNEL_SECRET`
  (or `UX_BEHAVIOR_SECRET`) must be set. A host without ux-channel still
  gets `None` from `attach()` when no secret is configured: the missing
  package is reported before the secret check.
- The public constant is refused even when passed explicitly.
- Dev Caps don't survive a restart. The per-process secret is minted once
  in that process and is not written anywhere. Set `UX_CHANNEL_SECRET`
  even in dev when using `--workers` greater than 1, `--reload`, or
  `REDIS_URL`. `REDIS_URL` with no configured secret raises even when
  `DEBUG=1`, because that store is shared by more than one process.
- `_trusted` in payloads is dropped, and the trust argument now takes the
  sentinel. `dispatch(action, **body)`, `submit(action, body)`, and an
  explicit `_trusted=True` / `"yes"` / `1` do not grant trust. An ignored
  body value is logged. `app.trust()` is unchanged. `wire/attach.py`
  passes the private sentinel only after Channel accepts the Cap. Reason:
  a host that spread request JSON into `dispatch` ran a capped action
  when the body contained `_trusted`.

### Fixed

- An omitted default is not type-checked. `b: Box = None` with `b` left
  out stays accepted, and the default is still passed to the action.
  Only values the caller actually passed are checked. Reason: resolving
  hints per parameter started rejecting defaults the caller never sent.
- Action argument checks resolve each parameter annotation on its own.
  `list[int]` stays a pass-through. One annotation that cannot be
  resolved no longer skips the other parameters, so `n: int` is still
  checked beside an unresolvable sibling. Reason: `get_type_hints()` on
  the whole callable raised for that one annotation, and the handler
  then dropped every hint.

## 0.4.1

### Removed — dead imports (no API change)

- Unused imports: `typing.Any` (`errors.py`), `typing.Mapping` and
  `planes.DictBackend` (`state_api.py`), `wire.compose.Conflict`
  (`wire/result.py`), plus unused imports and placeholder-less f-strings in tests.
- `tests/test_no_unused_imports.py` (stdlib only) keeps them gone.

### Kept on purpose

- `ComponentProtocol.__render__(pretty=False, **kw)` / `__async_render__` and the
  `Component` stubs keep `pretty` / `**kw`: they are the cross-library render
  protocol that ux-dom and ux-compose implement and call with `pretty=False`.
- `ActionMethod.__get__(obj, objtype=None)`: Python's descriptor protocol
  passes `objtype`; removing it would break class-level attribute access.

## 0.4.0

### Security (breaking)

- Attaching a Channel no longer disables the in-process Cap check.
  ``Behavior._require_caps`` used to return early whenever ``_wire`` was set, so
  any host code calling ``dispatch()`` on a capped action, for example an HTTP
  ``/act`` fall-through, ran it with no authority. Now only ``_trusted=True`` or
  ``strict_caps=False`` skips the check. The Channel handlers in
  ``wire/attach.py`` already pass ``_trusted=True`` after the Channel has
  verified the Cap, so the live path is unchanged. Migration: host code that
  dispatches a capped action after attach must go through the Channel
  (``submit_intent`` with a minted Cap) or pass ``_trusted=True`` on purpose.
- ``emit`` / ``async_emit`` no longer dispatch as trusted. A follow-up
  inherits the trust of the dispatch that armed it (stored on
  ``Continuation.trusted``), or the emitter's own ``app.trust()`` context.
  Migration: a public action that arms a protected finish needs the trusted
  host (e.g. a verified webhook) to emit inside ``app.trust()``.
- ``trust()`` is per context (contextvar), not a flip of the shared
  ``strict_caps``. Concurrent async requests outside the block stay checked,
  and ``strict_caps`` reads the same inside and outside.
- Continuations are single-use per context: the first ``emit`` disarms the
  event, and a second ``emit`` in that context raises ``ContinuationError``.
  Tasks forked after arming each hold their own copy, and separate requests
  cannot replay each other's follow-ups. Delivery is at-most-once: the event is
  removed before its action runs, so it is lost if the action fails or is
  refused. This is intentional, so a refund never runs twice. Only trusted host code may
  expose ``emit`` (see docs/reference/SECURITY.md).

### Changed

- Python floor raised to ≥3.14 (matches ux-compose / ux-dom). Classifiers are
  3.14-only.

### Removed

- Unused ``wire/caps.py`` ``CapMachine`` (OWNER-WRONG Cap crypto clone; zero
  importers). Cap mint/verify stays Channel. Absence-locked.

### Fixed

- ``bind_action_args`` binds the @action function, not ``BoundAction.__call__(*args, **kwargs)``.
  ``apply_defaults`` filling VAR_POSITIONAL as ``args=()`` made ``tick()`` raise
  ``unexpected keyword argument 'args'``. Channel ``args=dict`` unpacks unless
  the action declares a product parameter named ``args``.

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
