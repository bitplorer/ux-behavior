# Complex nested behaviors (near-complete product coverage)

Single patterns and simple nesting are not enough for real products. This document defines **full nested systems** that combine infinite scroll, optimistic UI, filters, tables, modals, drawers, chat, kanban, checkout, and notifications the way production websites actually do.

**How to read:** each system is one `Behavior`, many Components, deep ids, Host orchestration where multi-unit Ops must merge.

Related: [COMPLEX.md](COMPLEX.md) · [NESTED.md](NESTED.md) · [CATALOG.md](CATALOG.md)

---

## Coverage map (system → use cases)

| System | Primary products | Nested units |
|--------|------------------|--------------|
| **A. Commerce discovery** | Shopify-like storefronts | facets drawer + endless grid + product modal (tabs/gallery) + mini-cart + compare + toasts |
| **B. SaaS admin** | Linear/Notion/Stripe dashboards | shell nav + command palette + filterable table + bulk confirm + detail drawer + undo |
| **C. Social / media** | feeds, communities | endless feed + composer + thread modal + reactions + notif center |
| **D. Messaging** | support/inbox, chat apps | master list + conversation + composer + presence |
| **E. Work board** | Jira/Trello-like | kanban + card modal + checklist + comments |
| **F. Booking** | travel/local services | calendar + slot detail modal + checkout steps |
| **G. Content site** | docs/marketing | mega menu + tabs + accordion FAQ + consent + banner |

Together these approximate **almost all** nested interaction graphs on the public web.

---

## Global rules (every system)

```text
1. Deep ids:  modal.product.tabs  not  tabs
2. Morph = must repaint; Ref = silent token/id/pending
3. Nested dispatch Ops do NOT auto-merge — Host orchestrates opens
4. Async pages use _req token; ignore stale apply_*
5. Optimistic UI always has confirm/rollback path
6. Domain money/inventory never on client plane
7. Caps on domain mutations; open/close UI usually public
```

Host multi-open helper:

```python
def run_all(app, *calls):
    ops = []
    for name, kwargs in calls:
        ops.extend(app.dispatch(name, **(kwargs or {})) or [])
    return ops
```

---

## System A — Commerce discovery (nested)

**User journey:** filter → scroll grid → open product → switch tab / gallery → add to cart (optimistic) → compare → checkout modal.

```python
"""system_commerce.py"""
from __future__ import annotations
from ux_behavior import (
    Behavior, Component, MorphState, RefState, DictBackend,
    action, notify, go, open, close, follow_up,
)

class Facets(Component):
    id = "drawer.facets"
    open = MorphState(False)
    q = MorphState("")
    category = MorphState("all")

    def render(self):
        return f"<aside id='drawer.facets' data-open='{self.open}'></aside>"

    @action(caps=())
    def show(self):
        self.open = True
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        return None

    @action(caps=())
    def apply(self, q: str = "", category: str = "all"):
        self.q, self.category = q, category
        self.open = False
        # reset endless grid
        self._behavior.dispatch("grid.reset")
        self._behavior.dispatch("grid.more")
        return None

class Grid(Component):
    id = "grid"
    items = MorphState(())
    cursor = MorphState(None)
    has_more = MorphState(True)
    loading = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<div id='grid' data-n='{len(self.items or ())}' data-loading='{self.loading}'></div>"

    @action(caps=())
    def reset(self):
        self.items, self.cursor, self.has_more = (), None, True
        self.loading = False
        self._req = int(self._req or 0) + 1
        return None

    @action(caps=())
    def more(self):
        if self.loading or not self.has_more:
            return []
        self.loading = True
        self._req = int(self._req or 0) + 1
        return None  # Host fetch → apply_page

    @action(caps=())
    def apply_page(self, items: list | None = None, cursor=None, has_more: bool = True, token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.loading = False
        self.items = tuple(self.items or ()) + tuple(items or ())
        self.cursor, self.has_more = cursor, bool(has_more)
        return None

    @action(caps=())
    def open_product(self, id: str = ""):
        self._behavior.dispatch("modal.product.open", id=id)
        return None

class ProductModal(Component):
    id = "modal.product"
    open = MorphState(False)
    product_id = RefState("")

    def render(self):
        return f"<div id='modal.product' data-open='{self.open}'></div>"

    @action(caps=())
    def open(self, id: str = ""):
        self.product_id, self.open = id, True
        self._behavior.dispatch("modal.product.tabs.select", tab="overview")
        self._behavior.dispatch("modal.product.gallery.go", i=0)
        return [open("modal.product")]

    @action(caps=())
    def hide(self):
        self.open, self.product_id = False, ""
        return [close("modal.product")]

class ProductTabs(Component):
    id = "modal.product.tabs"
    tab = MorphState("overview")
    def render(self):
        return f"<div id='modal.product.tabs' data-tab='{self.tab}'></div>"
    @action(caps=())
    def select(self, tab: str = "overview"):
        self.tab = tab
        return None

class ProductGallery(Component):
    id = "modal.product.gallery"
    index = MorphState(0)
    def render(self):
        return f"<div id='modal.product.gallery' data-i='{self.index}'></div>"
    @action(caps=())
    def go(self, i: int = 0):
        self.index = int(i)
        return None
    @action(caps=())
    def next(self):
        self.index = int(self.index) + 1
        return None

class MiniCart(Component):
    id = "minicart"
    count = MorphState(0)
    open = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<div id='minicart' data-count='{self.count}' data-open='{self.open}'></div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.open = True
        self._req = int(self._req or 0) + 1
        return [notify("Added")]

    @action(caps=())
    def set_count(self, count: int = 0, token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.count = int(count)
        return None

class Compare(Component):
    id = "compare"
    ids = MorphState(())
    open = MorphState(False)
    def render(self):
        return f"<div id='compare' data-n='{len(self.ids or ())}'></div>"
    @action(caps=())
    def add(self, id: str = ""):
        ids = list(self.ids or ())
        if id not in ids and len(ids) < 4:
            ids.append(id)
        self.ids, self.open = tuple(ids), True
        return None

class Checkout(Component):
    id = "modal.checkout"
    open = MorphState(False)
    step = MorphState(1)
    status = MorphState("idle")
    def render(self):
        return f"<div id='modal.checkout' data-step='{self.step}' data-status='{self.status}'></div>"
    @action(caps=())
    def show(self):
        self.open, self.step, self.status = True, 1, "idle"
        return [open("modal.checkout")]
    @action(caps=())
    def start_pay(self):
        follow_up("paid", "modal.checkout.finish")
        self.status = "awaiting"
        return [notify("Pay now")]
    @action(caps=())
    def finish(self):
        self.status, self.open = "paid", False
        return [close("modal.checkout"), go("/thanks")]

def build_commerce() -> Behavior:
    app = Behavior.boot("Commerce")
    for C in (Facets, Grid, ProductModal, ProductTabs, ProductGallery, MiniCart, Compare, Checkout):
        app.add(C)
    return app
```

**Nested flow test**

```python
app = build_commerce()
app.dispatch("drawer.facets.apply", q="tee", category="men")
app.dispatch("grid.apply_page", items=[{"id":"1","title":"Tee"}], cursor=2, has_more=True, token=int(app.get("grid")._req or 0))
app.dispatch("grid.open_product", id="1")
assert app.get("modal.product").open and app.get("modal.product.tabs").tab == "overview"
app.dispatch("minicart.add", sku="1")
app.dispatch("modal.checkout.show")
app.dispatch("modal.checkout.start_pay")
app.emit("paid")
assert app.get("modal.checkout").status == "paid"
```

---

## System B — SaaS admin (nested)

**User journey:** command palette → filtered table → multi-select → bulk delete confirm → undo → row opens detail drawer.

```python
"""system_admin.py"""
from ux_behavior import Behavior, Component, MorphState, RefState, action, notify, go, follow_up

class Shell(Component):
    id = "shell"
    section = MorphState("items")
    def render(self):
        return f"<div id='shell' data-section='{self.section}'></div>"
    @action(caps=())
    def go_section(self, section: str = "items"):
        self.section = section
        return None

class Palette(Component):
    id = "palette"
    open = MorphState(False)
    query = MorphState("")
    def render(self):
        return f"<div id='palette' data-open='{self.open}'></div>"
    @action(caps=())
    def show(self):
        self.open, self.query = True, ""
        return None
    @action(caps=())
    def hide(self):
        self.open = False
        return None
    @action(caps=())
    def run(self, cmd: str = ""):
        self.open = False
        if cmd == "items":
            self._behavior.dispatch("shell.go_section", section="items")
        return None

class Table(Component):
    id = "table"
    q = MorphState("")
    sort_key = MorphState("created")
    sort_dir = MorphState("desc")
    selected = MorphState(())
    rows = MorphState(())
    page = MorphState(1)
    loading = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<table id='table' data-sel='{len(self.selected or ())}'></table>"

    @action(caps=())
    def search(self, q: str = ""):
        self.q, self.page = q, 1
        self._req = int(self._req or 0) + 1
        self.loading = True
        return None

    @action(caps=())
    def apply_rows(self, rows: list | None = None, token: int = 0):
        if token and token != int(self._req or 0):
            return []
        self.rows, self.loading = tuple(rows or ()), False
        return None

    @action(caps=())
    def toggle(self, id: str = ""):
        s = set(self.selected or ())
        s.symmetric_difference_update({id})
        self.selected = tuple(sorted(s))
        return None

    @action(caps=())
    def open_row(self, id: str = ""):
        self._behavior.dispatch("drawer.detail.open", id=id)
        return None

    @action(caps=())
    def ask_bulk_delete(self):
        self._behavior.dispatch("confirm.bulk.ask", ids=list(self.selected or ()))
        return None

class DetailDrawer(Component):
    id = "drawer.detail"
    open = MorphState(False)
    entity_id = RefState("")
    title = MorphState("")
    def render(self):
        return f"<aside id='drawer.detail' data-open='{self.open}'>{self.title}</aside>"
    @action(caps=())
    def open(self, id: str = ""):
        self.entity_id, self.open, self.title = id, True, ""
        return None  # Host loads title
    @action(caps=())
    def apply(self, title: str = ""):
        self.title = title
        return None
    @action(caps=())
    def hide(self):
        self.open = False
        return None

class BulkConfirm(Component):
    id = "confirm.bulk"
    open = MorphState(False)
    ids = RefState(())
    def render(self):
        return f"<div id='confirm.bulk' data-open='{self.open}'></div>"
    @action(caps=())
    def ask(self, ids: list | None = None):
        self.ids, self.open = tuple(ids or ()), True
        return None
    @action(caps=())
    def cancel(self):
        self.open, self.ids = False, ()
        return None
    @action(caps=("items.bulk_delete",))
    def confirm(self):
        ids = self.ids
        self.open, self.ids = False, ()
        self._behavior.get("table").selected = ()
        # arm undo
        self._behavior.dispatch("undo.show", label=f"Deleted {len(ids)}", payload={"ids": ids})
        return [notify(f"Deleted {len(ids)}")]

class Undo(Component):
    id = "undo"
    open = MorphState(False)
    label = MorphState("")
    payload = RefState(None)
    def render(self):
        return f"<div id='undo' data-open='{self.open}'>{self.label}</div>"
    @action(caps=())
    def show(self, label: str = "", payload=None):
        self.label, self.payload, self.open = label, payload, True
        follow_up("undo.expire", "undo.hide")
        return None
    @action(caps=())
    def hide(self):
        self.open, self.payload = False, None
        return None
    @action(caps=())
    def undo(self):
        data = self.payload
        self.open, self.payload = False, None
        return [notify("Restored")]  # Host restores data["ids"]

def build_admin() -> Behavior:
    app = Behavior.boot("Admin")
    for C in (Shell, Palette, Table, DetailDrawer, BulkConfirm, Undo):
        app.add(C)
    return app
```

---

## System C — Social feed (nested)

**User journey:** endless feed → like optimistic → open thread modal → reply → notifications badge.

```python
class Feed(Component):
    id = "feed"
    items = MorphState(())  # {id, body, likes, liked}
    cursor = MorphState(None)
    has_more = MorphState(True)
    loading = MorphState(False)
    _req = RefState(0)

    def render(self):
        return f"<div id='feed' data-n='{len(self.items or ())}'></div>"

    @action(caps=())
    def more(self):
        if self.loading or not self.has_more: return []
        self.loading = True
        self._req = int(self._req or 0) + 1
        return None

    @action(caps=())
    def apply_page(self, items=None, cursor=None, has_more=True, token=0):
        if token and token != int(self._req or 0): return []
        self.loading = False
        self.items = tuple(self.items or ()) + tuple(items or ())
        self.cursor, self.has_more = cursor, has_more
        return None

    @action(caps=())
    def like(self, id: str = ""):
        items = []
        for it in self.items or ():
            if it["id"] == id:
                liked = not it.get("liked")
                likes = int(it.get("likes") or 0) + (1 if liked else -1)
                it = {**it, "liked": liked, "likes": likes}
            items.append(it)
        self.items = tuple(items)
        return None  # Host persist / rollback

    @action(caps=())
    def open_thread(self, id: str = ""):
        self._behavior.dispatch("modal.thread.open", id=id)
        return None

class ThreadModal(Component):
    id = "modal.thread"
    open = MorphState(False)
    post_id = RefState("")
    replies = MorphState(())
    text = MorphState("")

    def render(self):
        return f"<div id='modal.thread' data-open='{self.open}'></div>"

    @action(caps=())
    def open(self, id: str = ""):
        self.post_id, self.open, self.replies, self.text = id, True, (), ""
        return None  # Host loads replies

    @action(caps=())
    def set_replies(self, replies=None):
        self.replies = tuple(replies or ())
        return None

    @action(caps=())
    def send(self, text: str = ""):
        body = (text or self.text or "").strip()
        if not body: return []
        self.replies = tuple(self.replies or ()) + ({{"id": "tmp", "body": body, "pending": True}},)
        self.text = ""
        return None

class Notifs(Component):
    id = "notifs"
    open = MorphState(False)
    unread = MorphState(0)
    items = MorphState(())
    def render(self):
        return f"<div id='notifs' data-unread='{self.unread}'></div>"
    @action(caps=())
    def push(self, id: str = "", text: str = ""):
        self.items = ({{"id": id, "text": text, "read": False}},) + tuple(self.items or ())
        self.unread = int(self.unread) + 1
        return None
```

---

## System D — Messaging inbox (nested)

```text
inbox.list  (master, selected_id)
  └─ chat.thread  (messages, pending send)
  └─ presence     (typing)
```

```python
class Inbox(Component):
    id = "inbox"
    threads = MorphState(())
    active = MorphState("")
    def render(self):
        return f"<div id='inbox' data-active='{self.active}'></div>"
    @action(caps=())
    def select(self, id: str = ""):
        self.active = id
        self._behavior.dispatch("chat.load", thread_id=id)
        return None

class Chat(Component):
    id = "chat"
    thread_id = RefState("")
    messages = MorphState(())
    text = MorphState("")
    _seq = RefState(0)
    def render(self):
        return f"<div id='chat' data-n='{len(self.messages or ())}'></div>"
    @action(caps=())
    def load(self, thread_id: str = ""):
        self.thread_id, self.messages, self.text = thread_id, (), ""
        return None
    @action(caps=())
    def send(self, text: str = ""):
        body = (text or self.text or "").strip()
        if not body: return []
        self._seq = int(self._seq or 0) + 1
        mid = f"local-{self._seq}"
        self.messages = tuple(self.messages or ()) + ({{"id": mid, "body": body, "pending": True}},)
        self.text = ""
        return None
```

---

## System E — Work board (nested)

```text
board
  └─ modal.card (title, column, checklist, comments)
```

```python
class Board(Component):
    id = "board"
    cards = MorphState(())  # {id, title, column}
    def render(self):
        return f"<div id='board'></div>"
    @action(caps=())
    def move(self, id: str = "", column: str = "todo"):
        self.cards = tuple({**c, "column": column} if c["id"] == id else c for c in (self.cards or ()))
        return None
    @action(caps=())
    def open_card(self, id: str = ""):
        self._behavior.dispatch("modal.card.open", id=id)
        return None

class CardModal(Component):
    id = "modal.card"
    open = MorphState(False)
    card_id = RefState("")
    title = MorphState("")
    checklist = MorphState(())  # {id, done, text}
    comments = MorphState(())
    def render(self):
        return f"<div id='modal.card' data-open='{self.open}'></div>"
    @action(caps=())
    def open(self, id: str = ""):
        self.card_id, self.open = id, True
        return None  # Host loads fields
    @action(caps=())
    def toggle_check(self, id: str = ""):
        self.checklist = tuple(
            {**x, "done": (not x["done"]) if x["id"] == id else x["done"]}
            for x in (self.checklist or ())
        )
        return None
```

---

## System F — Booking (nested)

```text
cal (month) → select day → modal.slots → modal.checkout steps
```

```python
class Cal(Component):
    id = "cal"
    year = MorphState(2026)
    month = MorphState(8)
    selected = MorphState("")
    def render(self):
        return f"<div id='cal' data-sel='{self.selected}'></div>"
    @action(caps=())
    def select_day(self, date: str = ""):
        self.selected = date
        self._behavior.dispatch("modal.slots.open", date=date)
        return None

class Slots(Component):
    id = "modal.slots"
    open = MorphState(False)
    date = MorphState("")
    slots = MorphState(())
    def render(self):
        return f"<div id='modal.slots' data-open='{self.open}'></div>"
    @action(caps=())
    def open(self, date: str = ""):
        self.date, self.open = date, True
        return None
    @action(caps=())
    def choose(self, slot: str = ""):
        self.open = False
        self._behavior.dispatch("modal.checkout.show", slot=slot, date=self.date)
        return None
```

---

## System G — Content / marketing site (nested)

```text
mega menu + page tabs + faq accordion + consent + banner
```

```python
class Mega(Component):
    id = "mega"
    open = MorphState(False)
    section = MorphState("")
    @action(caps=())
    def enter(self, section: str = ""):
        self.open, self.section = True, section
        return None
    @action(caps=())
    def leave(self):
        self.open, self.section = False, ""
        return None

class PageTabs(Component):
    id = "page.tabs"
    tab = MorphState("overview")
    @action(caps=())
    def select(self, tab: str = "overview"):
        self.tab = tab
        return None

class Faq(Component):
    id = "page.faq"
    open_id = MorphState("")
    @action(caps=())
    def toggle(self, id: str = ""):
        self.open_id = "" if self.open_id == id else id
        return None

class Consent(Component):
    id = "consent"
    seen = MorphState(False, backend="client", key="consent.seen")
    @action(caps=())
    def accept(self):
        self.seen = True
        return None
```

---

## Cross-system nesting matrix

| Nested pair | Where |
|-------------|--------|
| Endless list + facets | A, C |
| List + modal + tabs + gallery | A |
| Optimistic control + server confirm | A minicart, C like |
| Table + bulk + confirm + undo | B |
| Master list + detail drawer/chat | B, D |
| Board + card modal + checklist | E |
| Calendar + slots modal + checkout | F |
| Feed + thread modal + notifs | C |
| Palette + shell navigation | B |
| Mega + tabs + accordion + consent | G |
| Continuation pay | A checkout |
| Stale token apply_page | A, B, C |

---

## Host orchestration cheat-sheet

```python
# Open product with reset children
ops = []
ops += app.dispatch("modal.product.open", id=pid)
# child resets already inside open; if split:
# ops += app.dispatch("modal.product.tabs.select", tab="overview")

# Filter change resets infinite list
ops += app.dispatch("drawer.facets.apply", q=q, category=cat)
# facets.apply already calls grid.reset + grid.more

# Bulk delete with undo window
ops += app.dispatch("confirm.bulk.confirm")  # arms undo.show
# timer: app.emit("undo.expire")
```

---

## What this does *not* replace

| Still Host / Channel |
|----------------------|
| SQL, search index, object storage |
| Websocket fanout implementation |
| Cap crypto |
| CSS layout / focus traps / IO observers |

Behavior owns **interaction state + action graph + Ops**. The seven systems above compose into nearly all nested product UX graphs used on the modern web.
