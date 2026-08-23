# Contributing

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md). **Agent contract:** [AGENTS.md](AGENTS.md).

## Setup

Python **3.10+**. Layout: `src/ux_behavior`.

```bash
pip install -e ".[dev]"
```

Optional live Caps: `pip install -e ".[dev,channel]"`.

## Quality gate

```bash
pytest -q --ignore=tests/test_live_channel.py
uxbehavior doctor --fail
```

Full matrix:

```bash
pytest tests/test_examples_matrix.py tests/test_online_matrix.py \
       tests/test_parity_extra.py tests/test_every_mode.py -q
```

## Laws (do not regress)

See [DESIGN.md](DESIGN.md) and [AGENTS.md](AGENTS.md).

| Law | Statement |
|-----|-----------|
| Isolation | Only wire/door modules import `ux_channel` / `cek_*` |
| Cold import | `import ux_behavior` loads no Channel / CEK / codecs |
| XOR | On one Result: `morph(T)` XOR `scene.enter(T, html=…)` |
| Caps | `@action(..., caps=[...])`; `caps=()` is explicit public opt-out |
| Progressive disclosure | Wire helpers stay off top-level `__all__` |

## Docs

| File | May contain | Must not contain |
|------|-------------|------------------|
| `README.md` | Gate | Full API, ADR bodies |
| `START_HERE.md` | 5-minute first success | Exhaustive pattern catalog |
| `docs/tutorial/` | Learning narrative | API laundry lists |
| `docs/guides/` | Goal-oriented recipes | Conceptual essays as primary form |
| `docs/reference/` | Facts, signatures | Tutorial steps |
| `docs/internals/` | Why / architecture / C4 | Step lists as primary form |
| `docs/examples/` | Worked recipes | Law |
| `docs/adr/` | Architecture decisions | Mixed how-to |
| `DESIGN.md` | Binding decisions | Mixed how-to |

Map: [docs/INDEX.md](docs/INDEX.md). Keep [START.md](START.md) in sync with
START_HERE (short copy). Do not invent public names; `__init__.py` `__all__` wins.

## Pull requests

- Feature branches. Never commit directly to `main`. Never force-push `main`.
- Expanding `__all__` or exporting wire helpers at top level requires a new DESIGN entry.
- Tests for the matching mode (offline / online / Caps / async) in the same PR.
