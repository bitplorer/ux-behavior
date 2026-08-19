# Real-world UI behavior patterns

Production patterns for **ux-behavior**: state fields, actions, Ops, continuations.
Markup is illustrative HTML strings — swap for **ux-dom** in product Hosts.

| Pattern | File |
|---------|------|
| Tabs | [tabs.md](tabs.md) |
| Toasts / notices | [toasts.md](toasts.md) |
| Dropdown / menu | [dropdown.md](dropdown.md) |
| Modal / dialog | [modal.md](modal.md) |
| Carousel | [carousel.md](carousel.md) |
| Accordion | [accordion.md](accordion.md) |
| Drawer / sheet | [drawer.md](drawer.md) |
| Wizard / stepper | [wizard.md](wizard.md) |
| Pagination | [pagination.md](pagination.md) |
| Filters | [filters.md](filters.md) |
| Search typeahead | [typeahead.md](typeahead.md) |
| Confirm flows | [confirm.md](confirm.md) |
| Form suites | [forms.md](forms.md) |
| Nested chrome | [nested_chrome.md](nested_chrome.md) |
| Master catalog | [CATALOG.md](CATALOG.md) |

**Shared rules**

- Open/closed UI flags → `MorphState` (session) so morph repaints.
- Ephemeral animation tokens / request ids → `RefState`.
- User prefs (theme, density) → client Morph + `key=`.
- Durable drafts → store Morph + Host `app.state.use("store", …)`.
- Prefer `notify(...)` for one-shot toasts; prefer `open`/`close` chrome Ops for product chrome when Channel understands them.
