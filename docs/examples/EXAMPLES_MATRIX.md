# Mode matrix × every example family

For **each** pattern family in the repo, the same axes apply:

| Entry | Action kind | Caps | Authority |
|-------|-------------|------|-----------|
| `dispatch` / `submit` / `emit` | sync `@action` | public `()` | offline |
| `async_dispatch` / `async_submit` / `async_emit` | async `@action` | protected | trust / `_trusted` / live wire |

**Rule of thumb**

- **UI chrome** (tabs, menu, modal open, carousel, toasts queue) → almost always `caps=()`; matrix = sync + async entry both work; protected rarely used.
- **Domain mutations** (place order, bulk delete, pay finish, restore version) → `caps=("…",)`; matrix = refuse offline, allow trust/_trusted/live.
- **Mixed flows** (checkout start public + finish protected via emit) → public arm + trusted continuation.

Automated: `tests/test_examples_matrix.py`.

---

## Per-family matrix

### Widgets (`docs/patterns/*.md`)

| Example | Public actions | Protected actions | Sync | Async | Caps refuse | trust/_trusted | emit |
|---------|----------------|-------------------|------|-------|-------------|----------------|------|
| Tabs | `select` | — | yes | yes | n/a | n/a | n/a |
| Toasts | `push`, `dismiss` | — | yes | yes | n/a | n/a | optional expire |
| Dropdown | `toggle`, `choose` | — | yes | yes | n/a | n/a | n/a |
| Modal | `show`, `hide` | — | yes | yes | n/a | n/a | n/a |
| Carousel | `next`, `prev`, `go` | — | yes | yes | n/a | n/a | n/a |
| Accordion | `toggle` | — | yes | yes | n/a | n/a | n/a |
| Drawer | `show`, `hide` | — | yes | yes | n/a | n/a | n/a |
| Wizard | `next`, `back` | final `submit` optional | yes | yes | if capped | yes | n/a |
| Pagination | `set_page`, `more` | — | yes | yes | n/a | n/a | n/a |
| Filters | `set`, `clear` | — | yes | yes | n/a | n/a | n/a |
| Typeahead | `type`, `choose` | — | yes | yes | n/a | n/a | n/a |
| Confirm | `ask`, `cancel` | `confirm` | yes | yes | confirm | yes | n/a |
| Forms | `save` validation | save if domain | yes | yes | if capped | yes | n/a |

### Complex (`COMPLEX.md`)

| Example | Public | Protected | Sync/Async | Notes |
|---------|--------|-----------|------------|-------|
| Endless scroll | `more`, `apply_page` | — | both | Host fetch between |
| Optimistic like | `toggle` | optional persist | both | rollback public |
| Data table | sort/select | `bulk_delete` | both | Caps on bulk |
| Chat | `send`, `ack` | — | both | |
| Kanban | `move` | optional | both | |
| Upload | progress | — | both | |
| Command palette | `run` | optional cmds | both | |
| Undo | `show`, `undo` | — | both | emit expire |

### Nested systems (`COMPLEX_NESTED.md`)

| System | Public path | Protected path | Continuations |
|--------|-------------|----------------|---------------|
| A Commerce | facets, grid, product, cart.add | checkout.finish, pay | `paid` → finish |
| B Admin | table search, drawer | bulk_delete | undo.expire |
| C Social | feed.more, like | optional | |
| D Messaging | select, send | — | |
| E Board | move, open_card | — | |
| F Booking | select_day, slots | checkout | |
| G Content | mega, tabs, faq | — | |

### Residuals (`MORE_CASES.md`)

| Example | Typical Caps |
|---------|----------------|
| Tree select | public |
| Lightbox | public |
| Map pin | public |
| Inline save | optional protected |
| Versions restore | **protected** |
| Approval decide | **protected** |
| Coupon apply | public + Host validate |
| KYC submit | optional protected |
| Tenant switch | public |

### Mode-only (`EVERY_MODE.md`)

Full truth table for a single Demo component (sync/async × public/protected × trust).

---

## How to read a cell

```text
"Tabs select / async / public"
  → await app.async_dispatch("tabs.select", tab="specs")
  → runs offline, no Cap

"Confirm confirm / sync / protected / offline"
  → app.dispatch("confirm.confirm")
  → AuthorityError

"Confirm confirm / async / protected / _trusted"
  → await app.async_dispatch("confirm.confirm", _trusted=True)
  → runs
```

---

## Live column

For every protected cell, **live** means:

```text
attach(Channel) → inbound async_dispatch(..., _trusted=True)
control() may mint Cap for buttons
```

Without Channel, live column collapses to offline refuse for protected actions.
