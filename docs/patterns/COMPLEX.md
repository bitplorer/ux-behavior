# Complex production behaviors

Patterns used across modern marketing sites, SaaS, commerce, media, and social products. Each section is **Behavior-complete**: fields, actions, Ops, nesting notes, failure modes.

Markup is illustrative. Domain data stays on the Host.

---

## Index

| # | Pattern |
|---|--------|
| 1 | [Infinite / endless scroll](#1-infinite--endless-scroll) |
| 2 | [Virtualized list window](#2-virtualized-list-window) |
| 3 | [Optimistic UI](#3-optimistic-ui) |
| 4 | [Debounced search + cancel](#4-debounced-search--cancel) |
| 5 | [Faceted search + sticky filters + URL](#5-faceted-search--sticky-filters--url) |
| 6 | [Data table: sort, select, bulk](#6-data-table-sort-select-bulk) |
| 7 | [Master / detail split](#7-master--detail-split) |
| 8 | [Notification center + badge](#8-notification-center--badge) |
| 9 | [Activity / social feed](#9-activity--social-feed) |
| 10 | [Chat thread](#10-chat-thread) |
| 11 | [Kanban board](#11-kanban-board) |
| 12 | [Calendar month + events](#12-calendar-month--events) |
| 13 | [Upload progress](#13-upload-progress) |
| 14 | [Command palette](#14-command-palette) |
| 15 | [Mega menu](#15-mega-menu) |
| 16 | [Cookie / consent gate](#16-cookie--consent-gate) |
| 17 | [Onboarding checklist](#17-onboarding-checklist) |
| 18 | [Feature banner / announcement](#18-feature-banner--announcement) |
| 19 | [Comparison tray](#19-comparison-tray) |
| 20 | [Saved views / segments](#20-saved-views--segments) |
| 21 | [Multi-cart / mini-cart race](#21-multi-cart--mini-cart-race) |
| 22 | [Presence / typing indicator](#22-presence--typing-indicator) |
| 23 | [Skeleton & loading gates](#23-skeleton--loading-gates) |
| 24 | [Pull-to-refresh (mobile)](#24-pull-to-refresh-mobile) |
| 25 | [Undo snackbar](#25-undo-snackbar) |

---

## Shared production rules

```text
Loading flags     → MorphState (must repaint)
Request tokens    → RefState (ignore stale responses)
List pages/cursors→ MorphState session or store
Optimistic rows   → Morph patch first, confirm/rollback action later
Server pages      → Host fetches; Behavior only holds cursor + items projection
```

Stale response guard:

```python
req = RefState(0)

@action(caps=())
def load_more(self):
    self.req = int(self.req or 0) + 1
    token = self.req
    # Host async fetch... later:
    # if token != self.req: return []  # superseded
```

---

## 1. Infinite / endless scroll

**Sites:** feeds, catalogs, search results, admin logs.

```python
from ux_behavior import Component, MorphState, RefState, action, notify

class EndlessFeed(Component):
    id = "feed"
    items = MorphState(())          # tuple of {id, title}
    cursor = MorphState(None)       # opaque server cursor or page int
    has_more = MorphState(True)
    loading = MorphState(False)
    error = MorphState("")
    _req = RefState(0)

    def render(self):
        rows = "".join(f"<article data-id='{it['id']}'>{it['title']}</article>" for it in (self.items or ()))
        status = "loading" if self.loading else ("end" if not self.has_more else "ready")
        return f"<div id='feed' data-status='{status}' data-err='{self.error}'>{rows}</div>"

    @action(caps=())
    def reset(self):
        self.items = ()
        self.cursor = None
        self.has_more = True
        self.error = ""
        return None

    @action(caps=())
    def more(self):
        if self.loading or not self.has_more:
            return []
        self.loading = True
        self.error = ""
        self._req = int(self._req or 0) + 1
        token = self._req
        return None  # Host continues — see apply_page

    @action(caps=())
    def apply_page(self, items: list | None = None, cursor=None, has_more: bool = True, token: int = 0):
        """Host calls after fetch. token must match _req."""
        if token and token != int(self._req or 0):
            return []  # stale
        self.loading = False
        batch = tuple(items or ())
        self.items = tuple(self.items or ()) + batch
        self.cursor = cursor
        self.has_more = bool(has_more)
        return None

    @action(caps=())
    def fail(self, message: str = "Failed", token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.loading = False
        self.error = message
        return [notify(message, level="error")]
```

**Browser:** IntersectionObserver → `feed.more`. **Host:** async fetch using `cursor`, then `feed.apply_page`.

**Initial load:** `dispatch("feed.reset"); dispatch("feed.more")`.

---

## 2. Virtualized list window

**Sites:** large tables, mail inboxes.

Behavior holds **window**, not all rows:

```python
class VirtualList(Component):
    id = "vlist"
    offset = MorphState(0)       # first visible index
    limit = MorphState(30)
    total = MorphState(0)
    window = MorphState(())      # only visible slice projection

    def render(self):
        return f"<div id='vlist' data-offset='{self.offset}' data-total='{self.total}'></div>"

    @action(caps=())
    def set_window(self, offset: int = 0, limit: int = 30, total: int = 0, rows: list | None = None):
        self.offset = max(0, int(offset))
        self.limit = max(1, int(limit))
        self.total = max(0, int(total))
        self.window = tuple(rows or ())
        return None

    @action(caps=())
    def scroll_to(self, offset: int = 0):
        # Host re-queries slice [offset, offset+limit)
        self.offset = max(0, int(offset))
        return None
```

---

## 3. Optimistic UI

**Sites:** likes, follows, cart add, checkboxes.

```python
class LikeButton(Component):
    id = "like"
    count = MorphState(0)
    liked = MorphState(False)
    _pending = RefState(False)

    def render(self):
        return f"<button id='like' data-on='{self.liked}'>{self.count}</button>"

    @action(caps=())
    def toggle(self):
        if self._pending:
            return []
        # optimistically flip
        self.liked = not bool(self.liked)
        self.count = int(self.count) + (1 if self.liked else -1)
        self._pending = True
        return None  # Host API; then confirm or rollback

    @action(caps=())
    def confirm(self):
        self._pending = False
        return None

    @action(caps=())
    def rollback(self, liked: bool = False, count: int = 0):
        self.liked = liked
        self.count = count
        self._pending = False
        return [notify("Could not update", level="error")]
```

---

## 4. Debounced search + cancel

Debounce lives in the **browser**. Behavior still needs stale-token discard.

```python
class Search(Component):
    id = "search"
    query = MorphState("")
    hits = MorphState(())
    loading = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<div id='search' data-q='{self.query}' data-loading='{self.loading}'></div>"

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        self._req = int(self._req or 0) + 1
        if not q:
            self.hits = ()
            self.loading = False
            return None
        self.loading = True
        return None  # Host schedules search with token=self._req

    @action(caps=())
    def apply(self, hits: list | None = None, token: int = 0):
        if token != int(self._req or 0):
            return []
        self.loading = False
        self.hits = tuple(hits or ())
        return None
```

---

## 5. Faceted search + sticky filters + URL

```python
from ux_behavior import go

class Facets(Component):
    id = "facets"
    q = MorphState("")
    brands = MorphState(())      # tuple[str]
    price_min = MorphState(0)
    price_max = MorphState(0)
    sort = MorphState("relevance")

    def render(self):
        return f"<form id='facets' data-q='{self.q}'></form>"

    def _qs(self):
        brands = ",".join(self.brands or ())
        return f"?q={self.q}&brands={brands}&sort={self.sort}"

    @action(caps=())
    def set(self, q: str = "", brands: list | None = None, sort: str = "relevance",
            price_min: int = 0, price_max: int = 0):
        self.q = q
        self.brands = tuple(brands or ())
        self.sort = sort
        self.price_min = int(price_min)
        self.price_max = int(price_max)
        self._behavior.dispatch("results.reload")
        return [go("/shop" + self._qs())]

    @action(caps=())
    def toggle_brand(self, brand: str = ""):
        s = set(self.brands or ())
        if brand in s: s.remove(brand)
        else: s.add(brand)
        self.brands = tuple(sorted(s))
        self._behavior.dispatch("results.reload")
        return [go("/shop" + self._qs())]
```

---

## 6. Data table: sort, select, bulk

```python
class DataTable(Component):
    id = "table"
    sort_key = MorphState("created")
    sort_dir = MorphState("desc")
    selected = MorphState(())     # tuple ids
    page = MorphState(1)
    rows = MorphState(())

    def render(self):
        return f"<table id='table' data-sort='{self.sort_key}:{self.sort_dir}'></table>"

    @action(caps=())
    def sort(self, key: str = "created"):
        if self.sort_key == key:
            self.sort_dir = "asc" if self.sort_dir == "desc" else "desc"
        else:
            self.sort_key = key
            self.sort_dir = "asc"
        self.page = 1
        return None  # Host reloads rows

    @action(caps=())
    def toggle_row(self, id: str = ""):
        s = set(self.selected or ())
        if id in s: s.remove(id)
        else: s.add(id)
        self.selected = tuple(sorted(s))
        return None

    @action(caps=())
    def select_all(self, ids: list | None = None):
        self.selected = tuple(ids or ())
        return None

    @action(caps=())
    def clear_selection(self):
        self.selected = ()
        return None

    @action(caps=("items.bulk_delete",))
    def bulk_delete(self):
        ids = self.selected
        self.selected = ()
        # Host deletes ids; reload
        return [notify(f"Deleted {len(ids)} items")]
```

---

## 7. Master / detail split

```python
class Master(Component):
    id = "master"
    active_id = MorphState("")
    rows = MorphState(())

    def render(self):
        return f"<div id='master' data-active='{self.active_id}'></div>"

    @action(caps=())
    def select(self, id: str = ""):
        self.active_id = id
        self._behavior.dispatch("detail.load", id=id)
        return None

class Detail(Component):
    id = "detail"
    entity_id = RefState("")
    title = MorphState("")
    loading = MorphState(False)

    def render(self):
        return f"<div id='detail' data-loading='{self.loading}'>{self.title}</div>"

    @action(caps=())
    def load(self, id: str = ""):
        self.entity_id = id
        self.loading = True
        self.title = ""
        return None  # Host fills apply

    @action(caps=())
    def apply(self, title: str = ""):
        self.title = title
        self.loading = False
        return None
```

---

## 8. Notification center + badge

```python
class Notifications(Component):
    id = "notifs"
    open = MorphState(False)
    items = MorphState(())       # {id, text, read}
    unread = MorphState(0)

    def render(self):
        return f"<div id='notifs' data-open='{self.open}' data-unread='{self.unread}'></div>"

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return None

    @action(caps=())
    def push(self, id: str = "", text: str = ""):
        items = list(self.items or ())
        items.insert(0, {"id": id, "text": text, "read": False})
        self.items = tuple(items[:50])
        self.unread = int(self.unread) + 1
        return None

    @action(caps=())
    def mark_read(self, id: str = ""):
        items = []
        for it in self.items or ():
            if it["id"] == id and not it["read"]:
                it = {**it, "read": True}
                self.unread = max(0, int(self.unread) - 1)
            items.append(it)
        self.items = tuple(items)
        return None

    @action(caps=())
    def mark_all(self):
        self.items = tuple({**it, "read": True} for it in (self.items or ()))
        self.unread = 0
        return None
```

---

## 9. Activity / social feed

Combines endless scroll + optimistic react:

```python
class ActivityFeed(Component):
    id = "activity"
    items = MorphState(())
    cursor = MorphState(None)
    has_more = MorphState(True)
    loading = MorphState(False)

    # ... more/apply_page as in §1 ...

    @action(caps=())
    def react(self, id: str = "", kind: str = "like"):
        items = []
        for it in self.items or ():
            if it["id"] == id:
                reactions = dict(it.get("reactions") or {})
                reactions[kind] = int(reactions.get(kind, 0)) + 1
                it = {**it, "reactions": reactions}
            items.append(it)
        self.items = tuple(items)
        return None  # Host persists; rollback action if needed
```

---

## 10. Chat thread

```python
class Chat(Component):
    id = "chat"
    messages = MorphState(())    # {id, body, mine, pending}
    text = MorphState("")
    _seq = RefState(0)

    def render(self):
        return f"<div id='chat' data-n='{len(self.messages or ())}'></div>"

    @action(caps=())
    def type(self, text: str = ""):
        self.text = text
        return None

    @action(caps=())
    def send(self, text: str = ""):
        body = (text or self.text or "").strip()
        if not body:
            return []
        self._seq = int(self._seq or 0) + 1
        mid = f"local-{self._seq}"
        msg = {"id": mid, "body": body, "mine": True, "pending": True}
        self.messages = tuple(self.messages or ()) + (msg,)
        self.text = ""
        return None  # Host sends; ack with server id

    @action(caps=())
    def ack(self, local_id: str = "", server_id: str = ""):
        items = []
        for m in self.messages or ():
            if m["id"] == local_id:
                m = {**m, "id": server_id or local_id, "pending": False}
            items.append(m)
        self.messages = tuple(items)
        return None

    @action(caps=())
    def receive(self, id: str = "", body: str = ""):
        self.messages = tuple(self.messages or ()) + ({{"id": id, "body": body, "mine": False, "pending": False}},)
        return None
```

---

## 11. Kanban board

```python
class Board(Component):
    id = "board"
    columns = MorphState(("todo", "doing", "done"))
    # cards: {id, title, column}
    cards = MorphState(())

    def render(self):
        return f"<div id='board' data-cols='{len(self.columns or ())}'></div>"

    @action(caps=())
    def move(self, id: str = "", column: str = "todo"):
        if column not in set(self.columns or ()): 
            return []
        cards = []
        for c in self.cards or ():
            if c["id"] == id:
                c = {**c, "column": column}
            cards.append(c)
        self.cards = tuple(cards)
        return None  # Host persists order

    @action(caps=())
    def add(self, id: str = "", title: str = "", column: str = "todo"):
        self.cards = tuple(self.cards or ()) + ({{"id": id, "title": title, "column": column}},)
        return None
```

---

## 12. Calendar month + events

```python
class Calendar(Component):
    id = "cal"
    year = MorphState(2026)
    month = MorphState(8)          # 1-12
    selected = MorphState("")      # YYYY-MM-DD
    events = MorphState(())        # {id, date, title}

    def render(self):
        return f"<div id='cal' data-ym='{self.year}-{self.month}' data-sel='{self.selected}'></div>"

    @action(caps=())
    def shift(self, delta: int = 1):
        m = int(self.month) + int(delta)
        y = int(self.year)
        while m > 12: m -= 12; y += 1
        while m < 1: m += 12; y -= 1
        self.month = m
        self.year = y
        return None  # Host reloads events for month

    @action(caps=())
    def select_day(self, date: str = ""):
        self.selected = date
        return None

    @action(caps=())
    def set_events(self, events: list | None = None):
        self.events = tuple(events or ())
        return None
```

---

## 13. Upload progress

```python
class Uploader(Component):
    id = "upload"
    pct = MorphState(0)
    status = MorphState("idle")  # idle|running|done|error
    name = MorphState("")
    _job = RefState("")

    def render(self):
        return f"<div id='upload' data-pct='{self.pct}' data-status='{self.status}'></div>"

    @action(caps=())
    def start(self, name: str = "", job: str = ""):
        self.name = name
        self._job = job
        self.pct = 0
        self.status = "running"
        return None

    @action(caps=())
    def progress(self, pct: int = 0, job: str = ""):
        if job and job != self._job:
            return []
        self.pct = max(0, min(100, int(pct)))
        return None

    @action(caps=())
    def done(self, job: str = ""):
        if job and job != self._job:
            return []
        self.pct = 100
        self.status = "done"
        return [notify("Uploaded")]

    @action(caps=())
    def fail(self, job: str = "", message: str = "Upload failed"):
        if job and job != self._job:
            return []
        self.status = "error"
        return [notify(message, level="error")]
```

---

## 14. Command palette

```python
class Palette(Component):
    id = "palette"
    open = MorphState(False)
    query = MorphState("")
    hits = MorphState(())
    active = MorphState(0)

    def render(self):
        return f"<div id='palette' data-open='{self.open}'></div>"

    @action(caps=())
    def show(self):
        self.open = True
        self.query = ""
        self.hits = ()
        self.active = 0
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        return None

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        # Host filters commands
        return None

    @action(caps=())
    def set_hits(self, hits: list | None = None):
        self.hits = tuple(hits or ())
        self.active = 0
        return None

    @action(caps=())
    def run(self, id: str = ""):
        self.open = False
        return [go(f"/cmd/{id}")]
```

---

## 15. Mega menu

```python
class MegaMenu(Component):
    id = "mega"
    open = MorphState(False)
    section = MorphState("")  # which column

    def render(self):
        return f"<nav id='mega' data-open='{self.open}' data-section='{self.section}'></nav>"

    @action(caps=())
    def enter(self, section: str = ""):
        self.open = True
        self.section = section
        return None

    @action(caps=())
    def leave(self):
        self.open = False
        self.section = ""
        return None
```

---

## 16. Cookie / consent gate

```python
class Consent(Component):
    id = "consent"
    # client plane: remember choice
    seen = MorphState(False, backend="client", key="consent.seen")
    analytics = MorphState(False, backend="client", key="consent.analytics")

    def render(self):
        if self.seen:
            return "<div id='consent' hidden></div>"
        return "<div id='consent' role='dialog'>Cookies?</div>"

    @action(caps=())
    def accept_all(self):
        self.analytics = True
        self.seen = True
        return None

    @action(caps=())
    def reject(self):
        self.analytics = False
        self.seen = True
        return None
```

---

## 17. Onboarding checklist

```python
class Checklist(Component):
    id = "onboard"
    # store so progress survives
    done = MorphState((), backend="store")  # tuple step ids

    def render(self):
        return f"<div id='onboard' data-n='{len(self.done or ())}'></div>"

    @action(caps=())
    def complete(self, step: str = ""):
        s = set(self.done or ())
        s.add(step)
        self.done = tuple(sorted(s))
        return None
```

---

## 18. Feature banner / announcement

```python
class Banner(Component):
    id = "banner"
    dismissed = MorphState(False, backend="client", key="banner.v3")
    text = MorphState("New pricing")

    def render(self):
        if self.dismissed:
            return "<div id='banner' hidden></div>"
        return f"<div id='banner'>{self.text}</div>"

    @action(caps=())
    def dismiss(self):
        self.dismissed = True
        return None
```

---

## 19. Comparison tray

```python
class Compare(Component):
    id = "compare"
    ids = MorphState(())  # max 4
    open = MorphState(False)

    def render(self):
        return f"<div id='compare' data-n='{len(self.ids or ())}' data-open='{self.open}'></div>"

    @action(caps=())
    def add(self, id: str = ""):
        ids = list(self.ids or ())
        if id not in ids and len(ids) < 4:
            ids.append(id)
        self.ids = tuple(ids)
        self.open = True
        return None

    @action(caps=())
    def remove(self, id: str = ""):
        self.ids = tuple(x for x in (self.ids or ()) if x != id)
        if not self.ids:
            self.open = False
        return None
```

---

## 20. Saved views / segments

```python
class Views(Component):
    id = "views"
    active = MorphState("all")
    saved = MorphState((), backend="store")  # {id, name, query}

    @action(caps=())
    def select(self, id: str = "all"):
        self.active = id
        self._behavior.dispatch("results.reload")
        return None

    @action(caps=())
    def save(self, id: str = "", name: str = "", query: str = ""):
        rows = [x for x in (self.saved or ()) if x["id"] != id]
        rows.append({"id": id, "name": name, "query": query})
        self.saved = tuple(rows)
        self.active = id
        return [notify("View saved")]
```

---

## 21. Multi-cart / mini-cart race

```python
class MiniCart(Component):
    id = "minicart"
    count = MorphState(0)
    open = MorphState(False)
    _req = RefState(0)

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1  # optimistic
        self.open = True
        self._req = int(self._req or 0) + 1
        return None  # Host confirms true count via set_count

    @action(caps=())
    def set_count(self, count: int = 0, token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.count = int(count)
        return None
```

---

## 22. Presence / typing indicator

```python
class Presence(Component):
    id = "presence"
    typing = MorphState(())  # tuple user names
    online = MorphState(())

    @action(caps=())
    def set_typing(self, users: list | None = None):
        self.typing = tuple(users or ())
        return None

    @action(caps=())
    def set_online(self, users: list | None = None):
        self.online = tuple(users or ())
        return None
```

Host websocket → these actions; high-frequency updates may skip morph by using Ref + targeted Host patch if needed.

---

## 23. Skeleton & loading gates

```python
class PageGate(Component):
    id = "gate"
    phase = MorphState("loading")  # loading|ready|error

    def render(self):
        return f"<div id='gate' data-phase='{self.phase}'></div>"

    @action(caps=())
    def ready(self):
        self.phase = "ready"
        return None

    @action(caps=())
    def fail(self):
        self.phase = "error"
        return None
```

---

## 24. Pull-to-refresh (mobile)

```python
class Refreshable(Component):
    id = "ptr"
    refreshing = MorphState(False)

    @action(caps=())
    def refresh(self):
        if self.refreshing:
            return []
        self.refreshing = True
        return None  # Host reloads; then finish

    @action(caps=())
    def finish(self):
        self.refreshing = False
        return None
```

---

## 25. Undo snackbar

```python
from ux_behavior import follow_up

class UndoBar(Component):
    id = "undo"
    open = MorphState(False)
    label = MorphState("")
    payload = RefState(None)  # silent data for undo

    def render(self):
        if not self.open:
            return "<div id='undo' hidden></div>"
        return f"<div id='undo'>{self.label} <button>Undo</button></div>"

    @action(caps=())
    def show(self, label: str = "Deleted", payload=None):
        self.label = label
        self.payload = payload
        self.open = True
        follow_up("undo.expire", "undo.hide")
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        self.payload = None
        return None

    @action(caps=())
    def undo(self):
        data = self.payload
        self.open = False
        self.payload = None
        # Host restores data
        return [notify("Restored")]
```

Host timer → `emit("undo.expire")`.

---

## Production composition tips

| Concern | Practice |
|---------|----------|
| Scroll + filters | Reset cursor on filter change; `feed.reset` then `more` |
| Optimistic + endless | Optimistic patch item in `items` tuple by id |
| Table + bulk + confirm | `table.selected` + `confirm.bulk.ask` |
| Search + infinite | New query increments `_req` and clears items |
| Chat + presence | Separate components; different morph rates |

## Anti-patterns

| Avoid | Why |
|-------|-----|
| Holding 10k rows in MorphState | Use cursor + window / virtual window |
| No request token on async apply | Stale pages overwrite new queries |
| Money on client plane | `client_risk` + domain DB |
| One component for feed+filters+modal | Split ids; Host orchestrates |

This set matches the complex interaction surface of contemporary global websites when combined with the single patterns and [NESTED.md](NESTED.md) shell.
