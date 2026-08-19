# Real-world UI behavior patterns

## Nested systems (start here for composition)

**[NESTED.md](NESTED.md)** — Full nested real-world behaviors: id rules, state isolation, cross-dispatch, Ops merge, Caps, and a complete **commerce shell** (chrome + menu + drawer filters + catalog + product modal with tabs & carousel + confirm + checkout continuation + toasts).

## Single patterns

| Pattern | File |
|---------|------|
| Tabs | [tabs.md](tabs.md) |
| Toasts | [toasts.md](toasts.md) |
| Dropdown | [dropdown.md](dropdown.md) |
| Modal | [modal.md](modal.md) |
| Carousel | [carousel.md](carousel.md) |
| Accordion | [accordion.md](accordion.md) |
| Drawer | [drawer.md](drawer.md) |
| Wizard | [wizard.md](wizard.md) |
| Pagination | [pagination.md](pagination.md) |
| Filters | [filters.md](filters.md) |
| Typeahead | [typeahead.md](typeahead.md) |
| Confirm | [confirm.md](confirm.md) |
| Forms | [forms.md](forms.md) |
| Nested chrome (short) | [nested_chrome.md](nested_chrome.md) |
| Coverage catalog | [CATALOG.md](CATALOG.md) |

**Shared rules:** Morph for open/value; Ref for silent ids; `notify` for one-shot toasts; deep ids for nested units; Host orchestration when multiple units must morph together.
