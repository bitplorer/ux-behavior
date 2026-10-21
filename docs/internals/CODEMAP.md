# Code map — `codemap/`

> **Diátaxis:** explanation · **Layer:** ux-behavior
> Map: [INDEX.md](../INDEX.md).

[`codemap/`](codemap/index.json) is a generated, machine-readable map of
`src/ux_behavior`, one JSON shard per module: layers, imports, symbols, the
public API, entry points, features and the domain charter. CI fails when it is
stale or when the map has a problem.

[`scripts/codemap.py`](../../scripts/codemap.py) is vendored byte-identical
from ux-dom; `index.json` records its version and sha256. The full reference
(fields, config keys, checks) is ux-dom's
[CODEMAP.md](https://github.com/bitplorer/ux-dom/blob/main/docs/internals/CODEMAP.md).

## Rule

A PR updates the map in the same change as the code:

```bash
git add <new files>                      # consumers are read from tracked files
python scripts/codemap.py --write-changed
python scripts/codemap.py --check
```

## What is curated here

| File | Content |
|------|---------|
| `[tool.codemap]` in [pyproject.toml](../../pyproject.toml) | Layers (`core`, `behavior`, `wire`, `tooling`, `root`), layer rules, accepted exceptions |
| [features.toml](features.toml) | Features → modules, symbols, tests, docs |
| [domain.toml](domain.toml) | What this library owns, its public API, non-goals, and the exact ux-channel names it may use |

The layer rules keep `core` free of imports from the rest of the package and
make any new edge into `wire` a reviewed config change. `uxbehavior doctor`
still enforces the Isolation Law; the charter adds that every ux-channel name
used is listed in `domain.toml`.
