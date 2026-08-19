# Pattern catalog (coverage map)

Aim: **>99% of product UI behavior** expressible as Component state + actions + Ops.

| Use case | Primary state | Actions | Ops / notes |
|----------|---------------|---------|-------------|
| Tabs | `tab: MorphState` | `select(tab)` | morph panel |
| Pill tabs / underline | same | same | CSS only |
| Tabs + URL | session tab + `go(?tab=)` | select | optional nav Op |
| Toast single | — | — | `notify(msg)` |
| Toast queue | `queue: MorphState(list)` | `push`, `dismiss` | morph region |
| Toast auto-dismiss | queue + Ref timer id | push; Host JS or follow_up | |
| Dropdown | `open: MorphState(bool)` | `toggle`, `close` | morph |
| Menu select | open + `value` | `choose(v)` | close + morph |
| Combobox | open + query + value | `type`, `choose` | |
| Modal | `open` or chrome `open(id)` | `show`, `hide` | `open`/`close` Ops |
| Modal form | open + fields | `submit` | `submit_outcome` |
| Confirm delete | modal + target Ref | `ask`, `confirm` | continuation optional |
| Carousel index | `index: MorphState` | `next`, `prev`, `go(i)` | |
| Carousel autoplay | index + Ref playing | `play`, `pause` | Host timer → action |
| Accordion single | `open_id` | `toggle(id)` | |
| Accordion multi | `open_ids: list` | `toggle` | |
| Drawer | `open` | `show`, `hide` | |
| Wizard | `step` store/session | `next`, `back`, `goto` | |
| Pagination | `page`, `page_size` | `set_page` | |
| Infinite scroll | `page` + items store | `more` | append morph |
| Filters | dict Morph | `set`, `clear` | |
| Sort | `sort_key`, `dir` | `sort` | |
| Typeahead | query + hits + open | `type`, `choose` | debounce Host |
| Tree expand | `expanded: set` | `toggle` | |
| Table select | `selected: set` | `toggle_row` | |
| File progress | `pct` Morph | Host updates | |
| Theme | PrefState client | `set_theme` | |
| Locale | PrefState | `set_locale` | |
| Sidebar collapsed | Morph session | `toggle` | |
| Command palette | open + query | same as typeahead | |
| Popover | open + anchor Ref | toggle | |
| Tabs in modal | compose patterns | — | nested ids |

If a case is missing: express **open/value/query** as Morph, **timers/ids** as Ref, side effects as Ops.
