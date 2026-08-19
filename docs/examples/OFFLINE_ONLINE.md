# Offline vs online test parity

| Layer | File | What it proves |
|-------|------|----------------|
| **Offline matrix** | `tests/test_examples_matrix.py` | Public × sync/async entry, protected refuse/trust/_trusted, async actions, emit, validation, control |
| **Offline Demo law** | `tests/test_every_mode.py` | Full authority × sync/async truth table |
| **Online HTTP matrix** | `tests/test_online_matrix.py` | **Same public + protected + trusted + emit + validation** over real HTTP |
| **Channel (optional)** | `tests/test_live_channel.py` | Soft attach / Cap mint when `ux-channel` installed |

## Breadth claim

Online is **not** thinner on product examples:

- Every public family used offline is hit via `POST /dispatch`.
- Every protected action is **403** without trust and **200** with `trusted: true`.
- Async action on sync HTTP edge → **400 TypeError** (same law).
- Form validation + checkout `emit` match offline.

Channel crypto is optional; HTTP + `_trusted` is the always-on stand-in for “Channel already verified”.

```bash
pytest tests/test_examples_matrix.py tests/test_every_mode.py tests/test_online_matrix.py -q
```
