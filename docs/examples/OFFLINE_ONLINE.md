# Offline vs online example coverage (equal)

| Case | Offline `test_examples_matrix` | Online `test_online_matrix` (HTTP) |
|------|--------------------------------|-------------------------------------|
| Public widgets (tabs, toasts, modal, carousel, confirm.ask, grid, like, table, form, tree, versions, accordion, drawer, filters, typeahead, menu) | `dispatch` + `async_dispatch` | `POST /dispatch` + `POST /async_dispatch` |
| Public async actions | TypeError on sync; OK on async entry | TypeError on `/dispatch`; OK on `/async_dispatch` |
| Protected (confirm, bulk_delete, checkout.finish, versions.restore) | refuse / trust / `_trusted` | 403 / `trusted: true` → 200 |
| Protected on async entry | refuse / `_trusted` | `/async_dispatch` refuse / trusted |
| Form validation | sync + async entry | `/dispatch` + `/async_dispatch` |
| Checkout emit | `emit` + `async_emit` | `POST /emit` + `POST /async_emit` |
| control() | offline attrs | Host concern (no Cap offline) — intentional |
| Channel Cap mint | n/a | optional `test_live_channel.py` |

```bash
pytest tests/test_examples_matrix.py tests/test_online_matrix.py tests/test_every_mode.py -q
```
