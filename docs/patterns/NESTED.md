# Nested real-world behaviors

**Audience:** product engineers composing tabs, modals, drawers, menus, forms, carousels, toasts, wizards, and confirm flows **together** under one `Behavior`.

This document is the nested contract: how units nest, how state stays isolated, how actions cross boundaries, and full copy-paste systems that mirror production UI.

---

## 0. Mental model for nesting

```text
Behavior (one root per product surface)
├─ Component "chrome"          page, global menus
├─ Component "drawer.filters"  open + filter fields
├─ Component "catalog"         list driven by filters
├─ Component "modal.product"   open + product_id (Ref)
│   └─ logical child "modal.product.tabs"   tab Morph
├─ Component "toasts"          queue
└─ Component "confirm"         open + target Ref
```

**Facts (non-negotiable)**

1. Nesting is **logical**, not a React tree. Each Component is a registered unit with a **stable `id`**.
2. Parent does **not** automatically own child fields. Child MorphState lives on the child instance.
3. Cross-unit work is always: `app.dispatch("other.id.action", ...)` or Host reads `app.get("other.id")`.
4. Morph from action A only auto-refreshes **A’s** component unless you return explicit `update("other.id", html)`.
5. Prefer **deep ids**: `modal.product.tabs`, not a second global `tabs`.

---

## 1. ID and ownership rules

| Rule | Example |
|------|--------|
| Global chrome | `chrome`, `nav.main` |
| Overlay family | `modal.*`, `drawer.*` |
| Nested region | `modal.product.tabs`, `modal.product.gallery` |
| Ephemeral flow | `confirm.delete`, `wizard.onboard` |

**Do not** reuse `id="tabs"` in two places. Use `page.tabs` and `modal.product.tabs`.

---

## 2. State matrix when nested

| Concern | Field placement |
|---------|-----------------|
| Is modal open? | Parent modal Morph |
| Which tab inside modal? | Child tabs Morph |
| Which product is shown? | Parent Ref or Morph |
| Filter query for list | Drawer or catalog Morph |
| Confirm target id | Confirm Ref (silent) |
| Toast messages | Toasts Morph queue **or** `notify` only |

**Dirty isolation:** changing `modal.product.tabs.tab` does **not** by itself re-render `modal.product` unless the parent `render()` reads the child (unusual). Each unit morphs itself.

If the parent HTML **inlines** the child:

```python
def render(self):
    tabs_html = self._behavior.get("modal.product.tabs").render()
    return f"<div id='modal.product'>{tabs_html}</div>"
```

then parent must morph when child changes **or** child must be a separate morph target in the DOM (`id="modal.product.tabs"` sibling/region). **Recommended:** separate morph targets (child has its own root id in the page).

---

## 3. Cross-dispatch patterns

### 3.1 Parent opens and resets child

```python
@action(caps=())
def open_product(self, id: str = ""):
    self.product_id = id
    self.open = True
    # reset nested tab — explicit
    self._behavior.dispatch("modal.product.tabs.select", tab="overview")
    return None
```

Note: nested `dispatch` during an action **runs immediately** and may produce Ops that are **not** merged into the outer return. Prefer returning combined Ops or sequential Host orchestration.

**Safer Host orchestration:**

```python
def open_product_flow(app, product_id):
    ops = []
    ops += app.dispatch("modal.product.open_product", id=product_id)
    ops += app.dispatch("modal.product.tabs.select", tab="overview")
    return ops
```

### 3.2 Child requests parent close

```python
# on child
@action(caps=())
def done(self):
    return None  # Host also dispatches parent hide

# Host
app.dispatch("wizard.done")
app.dispatch("modal.wizard.hide")
```

### 3.3 Continuation across units

```python
# checkout starts pay; modal.pay is chrome
follow_up("paid", "checkout.complete")
return [open("modal.pay")]
# later emit("paid") → checkout.complete may close modal via close()
```

---

## 4. Composition catalog (99% nested cases)

| # | Composition | Units |
|---|-------------|-------|
| 1 | Page tabs | `page.tabs` |
| 2 | Modal alone | `modal.*` |
| 3 | Modal + tabs | `modal.x` + `modal.x.tabs` |
| 4 | Modal + form | `modal.x` fields on same or `modal.x.form` |
| 5 | Modal + confirm | `modal.x` + `confirm.*` |
| 6 | Drawer + filters + grid | `drawer.filters` + `catalog` |
| 7 | Dropdown → navigate | `menu` + `chrome.navigate` |
| 8 | Dropdown → modal | `menu.choose` → open modal |
| 9 | List row → modal detail | `catalog` + `modal.detail` |
| 10 | List row → confirm delete | `catalog` + `confirm.delete` |
| 11 | Wizard in modal | `modal.wizard` + `wizard.*` steps |
| 12 | Carousel in modal | `modal.product` + `modal.product.gallery` |
| 13 | Accordion in tab | `page.tabs` + `page.faq` |
| 14 | Toast after any | `notify` or `toasts.push` |
| 15 | Filters + pagination | `filters` + `list.page` |
| 16 | Typeahead → go | `search` + `nav` Op |
| 17 | Nested dropdown in modal | `modal.x` + `modal.x.menu` |
| 18 | Shell: nav + drawer + modal + toasts | full system below |
| 19 | Command palette over app | `palette` open + query |
| 20 | Split view master/detail | `master` + `detail` |

---

## 5. Full system: commerce shell (nested)

One Behavior, many units. This is the reference nested implementation.

```python
"""nested_commerce_shell.py — full nested behavior system."""
from __future__ import annotations

from ux_behavior import (
    Behavior, Component, MorphState, RefState, DictBackend,
    action, notify, go, open, close, update, follow_up, submit_outcome,
)

# ── chrome / navigation ──

class Chrome(Component):
    id = "chrome"
    page = MorphState("home")  # home | catalog | account

    def render(self):
        return f"<header id='chrome' data-page='{self.page}'></header>"

    @action(caps=())
    def navigate(self, page: str = "home"):
        self.page = page
        # close overlays that should not survive navigation
        self._behavior.dispatch("drawer.filters.hide")
        self._behavior.dispatch("menu.account.close")
        return None

# ── account dropdown ──

class AccountMenu(Component):
    id = "menu.account"
    open = MorphState(False)

    def render(self):
        return f"<div id='menu.account' data-open='{str(self.open).lower()}'></div>"

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return None

    @action(caps=())
    def close(self):
        self.open = False
        return None

    @action(caps=())
    def choose(self, item: str = ""):
        self.open = False
        if item == "profile":
            return [go("/account")]
        if item == "orders":
            self._behavior.dispatch("chrome.navigate", page="account")
            return None
        if item == "logout":
            return [notify("Signed out")]
        return None

# ── filters drawer + catalog ──

class FiltersDrawer(Component):
    id = "drawer.filters"
    open = MorphState(False)
    q = MorphState("")
    category = MorphState("all")
    sort = MorphState("popular")

    def render(self):
        return (
            f"<aside id='drawer.filters' data-open='{str(self.open).lower()}' "
            f"data-q='{self.q}' data-cat='{self.category}'></aside>"
        )

    @action(caps=())
    def show(self):
        self.open = True
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        return None

    @action(caps=())
    def apply(self, q: str = "", category: str = "all", sort: str = "popular"):
        self.q = q
        self.category = category
        self.sort = sort
        self.open = False
        # refresh list unit
        self._behavior.dispatch("catalog.reload")
        return None

    @action(caps=())
    def clear(self):
        self.q = ""
        self.category = "all"
        self.sort = "popular"
        self._behavior.dispatch("catalog.reload")
        return None


class Catalog(Component):
    id = "catalog"
    page = MorphState(1)
    # projection only — real rows from Host DB using filters
    rows = MorphState(())  # tuple of {id, title}

    def render(self):
        items = "".join(f"<li data-id='{r['id']}'>{r['title']}</li>" for r in (self.rows or ()))
        return f"<ul id='catalog' data-page='{self.page}'>{items}</ul>"

    @action(caps=())
    def reload(self):
        f = self._behavior.get("drawer.filters")
        # Host would query DB; demo filter in-memory
        all_rows = (
            {"id": "1", "title": "Alpha Tee", "category": "men"},
            {"id": "2", "title": "Beta Hat", "category": "women"},
            {"id": "3", "title": "Alpine Jacket", "category": "men"},
        )
        q = str(f.q or "").lower()
        cat = f.category
        out = []
        for r in all_rows:
            if cat != "all" and r["category"] != cat:
                continue
            if q and q not in r["title"].lower():
                continue
            out.append({"id": r["id"], "title": r["title"]})
        self.rows = tuple(out)
        self.page = 1
        return None

    @action(caps=())
    def open_product(self, id: str = ""):
        self._behavior.dispatch("modal.product.open", id=id)
        return None

    @action(caps=())
    def ask_delete(self, id: str = ""):
        self._behavior.dispatch("confirm.delete.ask", id=id)
        return None

    @action(caps=())
    def set_page(self, page: int = 1):
        self.page = max(1, int(page))
        return None

# ── product modal + nested tabs + nested carousel ──

class ProductModal(Component):
    id = "modal.product"
    open = MorphState(False)
    product_id = RefState("")

    def render(self):
        if not self.open:
            return "<div id='modal.product' hidden></div>"
        return (
            f"<div id='modal.product' role='dialog' data-pid='{self.product_id}'>"
            f"<!-- child morph targets: modal.product.tabs, modal.product.gallery -->"
            f"</div>"
        )

    @action(caps=())
    def open(self, id: str = ""):
        self.product_id = id
        self.open = True
        self._behavior.dispatch("modal.product.tabs.select", tab="overview")
        self._behavior.dispatch("modal.product.gallery.go", i=0)
        return [open("modal.product")]

    @action(caps=())
    def hide(self):
        self.open = False
        self.product_id = ""
        return [close("modal.product")]


class ProductTabs(Component):
    id = "modal.product.tabs"
    tab = MorphState("overview")  # overview | specs | reviews

    def render(self):
        return f"<div id='modal.product.tabs' data-tab='{self.tab}'></div>"

    @action(caps=())
    def select(self, tab: str = "overview"):
        if tab not in {"overview", "specs", "reviews"}:
            return []
        self.tab = tab
        return None


class ProductGallery(Component):
    id = "modal.product.gallery"
    index = MorphState(0)
    slides = MorphState(("img0", "img1", "img2"))

    def render(self):
        n = max(1, len(self.slides or ()))
        i = int(self.index) % n
        return f"<div id='modal.product.gallery' data-index='{i}'></div>"

    @action(caps=())
    def next(self):
        n = max(1, len(self.slides or ()))
        self.index = (int(self.index) + 1) % n
        return None

    @action(caps=())
    def prev(self):
        n = max(1, len(self.slides or ()))
        self.index = (int(self.index) - 1) % n
        return None

    @action(caps=())
    def go(self, i: int = 0):
        n = max(1, len(self.slides or ()))
        self.index = int(i) % n
        return None

# ── confirm delete ──

class ConfirmDelete(Component):
    id = "confirm.delete"
    open = MorphState(False)
    target_id = RefState("")

    def render(self):
        if not self.open:
            return "<div id='confirm.delete' hidden></div>"
        return f"<div id='confirm.delete' role='dialog'>Delete {self.target_id}?</div>"

    @action(caps=())
    def ask(self, id: str = ""):
        self.target_id = id
        self.open = True
        return None

    @action(caps=())
    def cancel(self):
        self.open = False
        self.target_id = ""
        return None

    @action(caps=())
    def confirm(self):
        tid = self.target_id
        self.open = False
        self.target_id = ""
        # Host deletes; refresh catalog
        self._behavior.dispatch("catalog.reload")
        return [notify(f"Deleted {tid}")]

# ── checkout nested in modal + continuation ──

class CheckoutModal(Component):
    id = "modal.checkout"
    open = MorphState(False)
    step = MorphState(1, backend="session")  # 1 address 2 pay 3 done
    status = MorphState("idle")

    def render(self):
        return (
            f"<div id='modal.checkout' data-open='{str(self.open).lower()}' "
            f"data-step='{self.step}' data-status='{self.status}'></div>"
        )

    @action(caps=())
    def show(self):
        self.open = True
        self.step = 1
        self.status = "idle"
        return [open("modal.checkout")]

    @action(caps=())
    def hide(self):
        self.open = False
        return [close("modal.checkout")]

    @action(caps=())
    def next_step(self):
        self.step = min(3, int(self.step) + 1)
        return None

    @action(caps=())
    def start_pay(self):
        follow_up("paid", "modal.checkout.finish")
        self.status = "awaiting_payment"
        return [notify("Complete payment")]

    @action(caps=())
    def finish(self):
        self.status = "paid"
        self.step = 3
        self.open = False
        return [close("modal.checkout"), go("/thanks"), notify("Paid")]

# ── toasts (optional queue) ──

class Toasts(Component):
    id = "toasts"
    items = MorphState(())
    _seq = RefState(0)

    def render(self):
        return f"<div id='toasts' data-n='{len(self.items or ())}'></div>"

    @action(caps=())
    def push(self, message: str = "", level: str = "info"):
        self._seq = int(self._seq or 0) + 1
        items = list(self.items or ())
        items.append({"id": str(self._seq), "message": message, "level": level})
        self.items = tuple(items)
        return None

    @action(caps=())
    def dismiss(self, id: str = ""):
        self.items = tuple(x for x in (self.items or ()) if x["id"] != id)
        return None


def build() -> Behavior:
    app = Behavior.boot("CommerceShell")
    app.state.use("store", DictBackend(), lock=True, source="host")
    for C in (
        Chrome, AccountMenu, FiltersDrawer, Catalog,
        ProductModal, ProductTabs, ProductGallery,
        ConfirmDelete, CheckoutModal, Toasts,
    ):
        app.add(C)
    app.dispatch("catalog.reload")
    return app


def demo():
    app = build()
    # filters nested with catalog
    app.dispatch("drawer.filters.show")
    app.dispatch("drawer.filters.apply", q="alp", category="men", sort="popular")
    assert any("Alpine" in r["title"] for r in app.get("catalog").rows)

    # list → product modal → tabs → gallery
    app.dispatch("catalog.open_product", id="3")
    assert app.get("modal.product").open is True
    assert app.get("modal.product.tabs").tab == "overview"
    app.dispatch("modal.product.tabs.select", tab="specs")
    app.dispatch("modal.product.gallery.next")
    assert int(app.get("modal.product.gallery").index) == 1

    # confirm nested flow
    app.dispatch("catalog.ask_delete", id="2")
    assert app.get("confirm.delete").open is True
    app.dispatch("confirm.delete.confirm")

    # checkout nested wizard + continuation
    app.dispatch("modal.checkout.show")
    app.dispatch("modal.checkout.next_step")
    app.dispatch("modal.checkout.start_pay")
    app.emit("paid")
    assert app.get("modal.checkout").status == "paid"

    # menu nested with chrome
    app.dispatch("menu.account.toggle")
    app.dispatch("menu.account.choose", item="orders")
    assert app.get("chrome").page == "account"

    print("nested demo ok", app.diagnostics.summary()["counts"])


if __name__ == "__main__":
    demo()
```

---

## 6. Behavior of nested dispatch (important)

When action A calls `self._behavior.dispatch("B.act")`:

| Effect | Detail |
|--------|--------|
| B runs fully | Caps, validation, dirty morph for **B** |
| Ops from B | Returned to A’s caller **only if A returns them** |
| Default | Inner Ops are **discarded** unless A captures return value |

**Correct merge:**

```python
@action(caps=())
def open_product(self, id: str = ""):
    self.open = True
    self.product_id = id
    ops = list(self._behavior.dispatch("modal.product.tabs.select", tab="overview") or [])
    # parent dirty morph if return None — conflict: if you return ops, parent auto-morph skips
    ops += [update("modal.product", self.render())]  # explicit
    return ops
```

**Host-level merge (clearest for production):**

```python
def open_product(app, id):
    return (
        app.dispatch("modal.product.open", id=id)
        + app.dispatch("modal.product.tabs.select", tab="overview")
        + app.dispatch("modal.product.gallery.go", i=0)
    )
```

Wire/HTTP handlers should use Host orchestration for multi-unit opens.

---

## 7. Nested chrome Ops vs Morph flags

| Approach | When |
|----------|------|
| `MorphState open` on component | You own HTML for the overlay |
| `return [open("modal.x")]` | Product chrome / Channel applies overlay cell |
| Both | Morph flag for local render **and** chrome Ops for shell |

Avoid double source of truth: either Host chrome owns visibility **or** component Morph does. If both, keep them updated together in the same action.

---

## 8. Nested Caps

```text
catalog.open_product     caps=()        # opens UI
confirm.delete.confirm   caps=("items.delete",)
modal.checkout.start_pay caps=("checkout.pay",)
```

Opening UI is usually public; **mutating domain** actions stay protected.

---

## 9. Nested testing checklist

1. Open modal resets child tab + gallery index  
2. Apply filters closes drawer and reloads catalog  
3. Delete confirm only deletes after confirm  
4. Navigate closes drawer + menu  
5. Checkout emit finishes and closes modal  
6. Child morph targets exist as separate ids in HTML  
7. Protected confirm refuses offline without trust  
8. Diagnostics show CONTINUATION_ARMED on start_pay  

---

## 10. Anti-patterns

| Anti-pattern | Do instead |
|--------------|------------|
| One Component with 40 fields for whole page | Split units by id |
| Child id `tabs` reused in modal and page | Prefix `modal.*.tabs` |
| Rely on nested dispatch Ops without merge | Host orchestration |
| Money on client Morph inside modal | store/session or Host DB |
| Silent `except` around nested dispatch | Let errors surface + diagnostics |

---

## 11. Quick recipe index

| Need | Recipe |
|------|--------|
| Modal with tabs + carousel | §5 ProductModal + Tabs + Gallery |
| Drawer filters driving list | FiltersDrawer.apply → catalog.reload |
| Row delete with confirm | catalog.ask_delete → confirm.* |
| Pay flow nested in modal | CheckoutModal + follow_up/emit |
| Menu drives page | menu.choose → chrome.navigate |
| Toast without Morph | `return [notify(...)]` |
| Toast queue UI | `toasts.push` |

This set covers the nested combinations used in typical commerce, SaaS, and content product shells. Extend by adding units; do not collapse nesting into one mega-component.
