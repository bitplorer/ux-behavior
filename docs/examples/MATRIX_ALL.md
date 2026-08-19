# Mode matrix — every pattern / example

**Rule:** for each action in each example, the same authority × entry-point matrix applies.

```text
Entry:   dispatch | async_dispatch | submit | async_submit | emit | async_emit
Caps:    public caps=()  |  protected caps=("…",)
Auth:    offline  |  trust()  |  _trusted=True  |  live Channel attach
Action:  sync def  |  async def
```

## Compatibility (library law)

| Action kind | `dispatch` / `submit` / `emit` | `async_*` |
|-------------|-------------------------------|-----------|
| Sync `@action` | runs | runs |
| Async `@action` | **TypeError** | runs |

## Authority (library law)

| Caps | Offline | `trust()` / `_trusted` | Live Channel (valid Cap) |
|------|---------|------------------------|---------------------------|
| `()` public | allow | allow | allow |
| `("dom.write",)` | **AuthorityError** | allow | allow if Cap verifies |

`emit` / `async_emit` always dispatch the continuation with `_trusted=True`.

---

## Per-pattern expected Caps

Public chrome and navigation stay `caps=()`. Domain mutations take Caps. Patterns without a protected action still appear in the matrix so **public × sync × async** is proven.

### Widgets (`docs/patterns/`)

| Pattern | Public actions | Protected actions (typical Cap) |
|---------|----------------|----------------------------------|
| Tabs | `select` | — |
| Toasts | `push`, `dismiss` | — |
| Dropdown | `toggle`, `pick`, `close` | — |
| Modal | `show`, `hide` | `submit` → `forms.write` when form commits |
| Carousel | `next`, `prev`, `go` | — |
| Accordion | `toggle`, `open_only` | — |
| Drawer | `open`, `close` | — |
| Wizard | `next`, `back` | `finish` → `flow.write` |
| Pagination | `go_page`, `next`, `prev` | — |
| Filters | `set`, `apply`, `reset` | — |
| Typeahead | `type`, `apply_hits`, `pick` | — |
| Confirm | `ask`, `cancel` | `yes` → `destructive.write` |
| Forms | field edits (public) | `save` / `submit` → `forms.write` |
| Nested chrome | open/close parents | child domain saves |

### Complex (`COMPLEX.md`)

| Pattern | Public | Protected |
|---------|--------|-----------|
| Endless scroll | `reset`, `more`, `apply_page` | — (reads); writes elsewhere |
| Virtual list | `scroll_to` | — |
| Optimistic like | — | `toggle_like` → `social.write` |
| Typeahead | as widgets | — |
| Faceted search | filter apply | — |
| Bulk grid | `toggle`, `select_all`, `clear` | `bulk_delete` → `catalog.write` |
| Autosave | `edit` | `save` → `docs.write` |
| Undo archive | — | `archive`, `undo` → `mail.write` |
| Master–detail | `select` | detail `save` |
| Kanban | — | `move` → `board.write` |
| Chat | draft | `send` → `chat.write` |
| Notices | `open_panel`, `push` | — |
| Upload | `tick` | `start` → `files.write` |
| Checkout | preview | `pay` / `fulfill` → `orders.write` |
| Theme / locale | `set_theme` | — |
| Command palette | `toggle`, `run` | `run` may target protected |
| Cart qty | — | `set_qty` → `cart.write` |

### Nested systems (`COMPLEX_NESTED.md`)

| System | Public surface | Protected surface |
|--------|----------------|-------------------|
| A Commerce | facets, grid pages, open product, tabs | cart writes, checkout, pay |
| B SaaS admin | shell nav, table select | bulk_delete, detail save |
| C Social | feed scroll | like, reply |
| D Messaging | open thread | send |
| E Board | open card | move, checklist write |
| F Booking | month nav | hold slot, pay |
| G Content | menu, tabs, accordion | — |

### Residuals (`MORE_CASES.md`)

| Case | Public | Protected |
|------|--------|-----------|
| Tree browser | expand, select | rename/delete |
| Lightbox | open, next, close | — |
| Map + panel | select pin | save place |
| Inline edit | start, cancel | commit |
| Tags | add UI | persist tags |
| Date range | set range | — |
| Theme/locale | set | — |
| Session timeout | warn, extend | step-up auth |
| Tour | next, skip | — |
| Offline queue | list | flush → domain Caps |
| Tenant switch | select | switch → `tenant.write` |
| Version restore | list | restore |
| Approval | view | approve/reject |
| Coupon | apply preview | redeem |
| KYC | step UI | submit step |
| Share sheet | open, copy | — |

---

## Required checks per action

For **every public** action in the tables above:

| # | Mode | Expect |
|---|------|--------|
| P1 | offline + `dispatch` | success `list[Op]` |
| P2 | offline + `async_dispatch` | success |
| P3 | offline + `submit` / `async_submit` | same |

For **every protected** action:

| # | Mode | Expect |
|---|------|--------|
| X1 | offline + `dispatch` | `AuthorityError` |
| X2 | offline + `async_dispatch` | `AuthorityError` |
| X3 | offline + `with trust(): dispatch` | success |
| X4 | offline + `with trust(): async_dispatch` | success |
| X5 | offline + `dispatch(..., _trusted=True)` | success |
| X6 | offline + `async_dispatch(..., _trusted=True)` | success |
| X7 | if continuation: `emit` / `async_emit` | success (trusted) |

Optional live (Channel installed):

| # | Mode | Expect |
|---|------|--------|
| L1 | attach + control mint + dispatch with Cap | success |
| L2 | attach missing Cap | refuse |

---

## Runnable catalog

| Artifact | Role |
|----------|------|
| `docs/examples/EVERY_MODE.md` | Law + Demo component |
| `docs/examples/MATRIX_ALL.md` | This file — per-pattern Caps map |
| `tests/test_every_mode.py` | Law tests (Demo) |
| `tests/test_matrix_all_patterns.py` | Parametrized public/protected × sync/async over pattern fixtures |
| `examples/harbor_cart_pilot.py` | Live-shaped pilot |

```bash
pytest tests/test_every_mode.py tests/test_matrix_all_patterns.py -q
```

---

## Authoring rule for new examples

1. Mark chrome/read `caps=()`.
2. Mark money, delete, pay, send, approve `caps=("domain.verb",)`.
3. Add one row to the tables above.
4. Extend `test_matrix_all_patterns.py` fixture list (public id + protected id).
5. Never document a protected action as runnable offline without `trust` / Channel.
