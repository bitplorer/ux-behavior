# State planes — claims must equal code

**Council binding decision (2026-08-19)**

## Verdict

| Option | Decision |
|--------|----------|
| A Shrink claims to match code | **Accepted (primary)** |
| B Full ux-app plane backends in behavior | **Rejected** (re-creates App runtime; Channel/Host own live mirrors) |
| C Collapse to one marker | **Rejected** (migration + intent labels still useful) |
| D Hybrid | **Accepted (minimal)** — TransientState skips dirty projection |

## What the names claim (author intent)

| Marker | Intent label |
|--------|----------------|
| `SessionState` | UI chrome / screen state |
| `ClientState` | Browser preference (`key=` reserved) |
| `StoreState` | Component-local kept value |
| `TransientState` | Ephemeral |

## What the code does

| Behavior | Session / Client / Store | Transient |
|----------|--------------------------|-----------|
| Storage | `instance.__dict__` | same |
| Dirty projection | **yes** if value changes and action returns `None` | **no** (excluded from snapshot) |
| Channel draft | no | no |
| world.kv | no | no |
| Browser client ops | no | no |

## Forbidden claims

Docs, READMEs, and harbor pilot text must **not** say offline `SessionState` is Channel session, or that `StoreState` writes kv, or that `ClientState` pushes browser prefs — until a wire/Host implementation exists and tests prove it.

## Residual disagreement

- Minority: implement real session draft soon for harbor parity.
- Majority: Host/Channel own that; behavior stays label-accurate and isolation-clean.
