# Live checks

## Quick run

```bash
pip install -e ".[dev]"
pip install -e "git+https://github.com/bitplorer/ux-channel.git#subdirectory=python#egg=ux-channel"
pip install fastapi httpx
pytest tests/test_live_channel.py -q
# full suite (live tests skip if Channel missing)
pytest -q
uxbehavior doctor --fail
```

## Coverage (when Channel present)

| Check | Status |
|-------|--------|
| `probe()` / `present()` | Channel detected |
| `dispatch` dirty projection | morph Op |
| `dispatch` explicit Ops | morph + notify |
| stamp rejects unstamped pair | PermissionError |
| `attach(FastAPI())` | Channel instance, idempotent |
| `attach(None)` | soft None |
| chrome open/close | kv + morph |
| Result XOR | Conflict on morph + transition html |
| Result navigate last | ordered |
| doctor | clean |

## Harbor pilot

```bash
cd harbor
pip install -e ".[dev]"
pytest tests/test_behavior_pilot.py -q
export HARBOR_BEHAVIOR_PILOT=1
# import app.host → behavior_host populated when flag set
```

## Notes

- Channel install path uses `#subdirectory=python`.
- Live suite uses `importorskip` so CI without Channel still passes unit tests.
- Full HTTP Intent→Action through Channel peer is Host/product work; this suite validates the **Behavior ↔ Channel attach door** and author Ops laws.
