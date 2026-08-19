# Residual use cases (everything still common on the web)

Patterns **not** fully spelled out in COMPLEX / COMPLEX_NESTED / single widgets, but used widely. Each is Behavior-shaped: Morph/Ref + actions + Ops notes.

---

## Index of residuals

| # | Case |
|---|------|
| 1 | Tree / file browser |
| 2 | Lightbox / media viewer |
| 3 | Map + selected pin + side panel |
| 4 | Inline edit (contenteditable / pencil) |
| 5 | Tags / chips input |
| 6 | Date range picker |
| 7 | Theme + locale + currency switchers |
| 8 | Session timeout / step-up auth modal |
| 9 | Product tour / coach marks |
| 10 | Offline queue / retry banner |
| 11 | Tenant / workspace switcher |
| 12 | Document version history + restore |
| 13 | Approval workflow states |
| 14 | Coupon / gift card apply |
| 15 | KYC / document capture steps |
| 16 | Share sheet |
| 17 | Split pane resize |
| 18 | Color / size variant picker (PDP) |
| 19 | Quantity stepper |
| 20 | Star rating input |
| 21 | Pin / favorite board |
| 22 | Watch / subscribe toggle |
| 23 | Multi-file attachment list |
| 24 | Code / diff viewer tabs |
| 25 | Timeline / vertical stepper |
| 26 | Floating action button menu |
| 27 | Bottom nav (mobile) |
| 28 | Auth magic-link wait state |
| 29 | Captcha / challenge gate |
| 30 | Maintenance / read-only banner |

---

## 1. Tree / file browser

```python
class Tree(Component):
    id = "tree"
    expanded = MorphState(())   # tuple node ids
    selected = MorphState("")
    # nodes supplied by Host in render context or Morph snapshot

    def render(self):
        return f"<div id='tree' data-sel='{self.selected}'></div>"

    @action(caps=())
    def toggle(self, id: str = ""):
        s = set(self.expanded or ())
        if id in s: s.remove(id)
        else: s.add(id)
        self.expanded = tuple(sorted(s))
        return None

    @action(caps=())
    def select(self, id: str = ""):
        self.selected = id
        self._behavior.dispatch("preview.load", id=id)
        return None
```

Nested: tree + preview panel (master/detail).

---

## 2. Lightbox / media viewer

```python
class Lightbox(Component):
    id = "lightbox"
    open = MorphState(False)
    index = MorphState(0)
    urls = MorphState(())

    def render(self):
        return f"<div id='lightbox' data-open='{self.open}' data-i='{self.index}'></div>"

    @action(caps=())
    def open_at(self, index: int = 0, urls: list | None = None):
        if urls is not None:
            self.urls = tuple(urls)
        self.index = int(index)
        self.open = True
        return None

    @action(caps=())
    def next(self):
        n = max(1, len(self.urls or ()))
        self.index = (int(self.index) + 1) % n
        return None

    @action(caps=())
    def close(self):
        self.open = False
        return None
```

---

## 3. Map + pin + panel

```python
class MapView(Component):
    id = "map"
    center_lat = MorphState(0.0)
    center_lng = MorphState(0.0)
    zoom = MorphState(12)
    selected = MorphState("")      # pin id

    def render(self):
        return f"<div id='map' data-pin='{self.selected}'></div>"

    @action(caps=())
    def select_pin(self, id: str = ""):
        self.selected = id
        self._behavior.dispatch("map.panel.open", id=id)
        return None

    @action(caps=())
    def pan(self, lat: float = 0, lng: float = 0, zoom: int = 12):
        self.center_lat, self.center_lng, self.zoom = lat, lng, zoom
        return None

class MapPanel(Component):
    id = "map.panel"
    open = MorphState(False)
    place_id = RefState("")
    title = MorphState("")

    @action(caps=())
    def open(self, id: str = ""):
        self.place_id, self.open = id, True
        return None
```

Map JS owns tiles; Behavior owns selection + panel.

---

## 4. Inline edit

```python
class InlineEdit(Component):
    id = "inline"
    editing = MorphState(False)
    value = MorphState("")
    draft = MorphState("")

    @action(caps=())
    def start(self):
        self.draft = self.value
        self.editing = True
        return None

    @action(caps=())
    def cancel(self):
        self.editing = False
        self.draft = self.value
        return None

    @action(caps=())
    def save(self, text: str = ""):
        self.value = text or self.draft
        self.editing = False
        return [notify("Saved")]
```

---

## 5. Tags / chips

```python
class Tags(Component):
    id = "tags"
    items = MorphState(())
    input = MorphState("")

    @action(caps=())
    def type(self, q: str = ""):
        self.input = q
        return None

    @action(caps=())
    def add(self, tag: str = ""):
        t = (tag or self.input or "").strip()
        if not t: return []
        items = list(self.items or ())
        if t not in items:
            items.append(t)
        self.items, self.input = tuple(items), ""
        return None

    @action(caps=())
    def remove(self, tag: str = ""):
        self.items = tuple(x for x in (self.items or ()) if x != tag)
        return None
```

---

## 6. Date range picker

```python
class DateRange(Component):
    id = "daterange"
    start = MorphState("")  # ISO date
    end = MorphState("")
    open = MorphState(False)

    @action(caps=())
    def set_range(self, start: str = "", end: str = ""):
        self.start, self.end, self.open = start, end, False
        self._behavior.dispatch("results.reload")
        return None
```

---

## 7. Theme / locale / currency

```python
class Prefs(Component):
    id = "prefs"
    theme = MorphState("system", backend="client", key="ui.theme")
    locale = MorphState("en", backend="client", key="ui.locale")
    currency = MorphState("USD", backend="client", key="ui.currency")

    @action(caps=())
    def set_theme(self, theme: str = "system"):
        self.theme = theme
        return None

    @action(caps=())
    def set_locale(self, locale: str = "en"):
        self.locale = locale
        return None

    @action(caps=())
    def set_currency(self, currency: str = "USD"):
        self.currency = currency
        return None
```

---

## 8. Session timeout / step-up auth

```python
class SessionGate(Component):
    id = "session.gate"
    locked = MorphState(False)
    reason = MorphState("")  # timeout | stepup

    @action(caps=())
    def lock(self, reason: str = "timeout"):
        self.locked, self.reason = True, reason
        return None

    @action(caps=())
    def unlock(self):
        self.locked, self.reason = False, ""
        return None
```

Host timers / 401 handlers call `lock`. Nested: modal password form inside gate.

---

## 9. Product tour / coach marks

```python
class Tour(Component):
    id = "tour"
    active = MorphState(False)
    step = MorphState(0)
    # progress durable
    completed = MorphState(False, backend="client", key="tour.v1.done")

    @action(caps=())
    def start(self):
        if self.completed: return []
        self.active, self.step = True, 0
        return None

    @action(caps=())
    def next(self):
        self.step = int(self.step) + 1
        return None

    @action(caps=())
    def finish(self):
        self.active, self.completed = False, True
        return None

    @action(caps=())
    def skip(self):
        self.active, self.completed = False, True
        return None
```

---

## 10. Offline queue / retry banner

```python
class Offline(Component):
    id = "offline"
    online = MorphState(True)
    queue = MorphState(())   # {id, action, args}

    @action(caps=())
    def set_online(self, online: bool = True):
        self.online = online
        if online and self.queue:
            return [notify(f"Retrying {len(self.queue)} actions")]
        return None

    @action(caps=())
    def enqueue(self, id: str = "", action: str = "", args: dict | None = None):
        self.queue = tuple(self.queue or ()) + ({{"id": id, "action": action, "args": args or {}}},)
        return None

    @action(caps=())
    def drain_ok(self, id: str = ""):
        self.queue = tuple(x for x in (self.queue or ()) if x["id"] != id)
        return None
```

---

## 11. Tenant / workspace switcher

```python
class Tenant(Component):
    id = "tenant"
    current = MorphState("", backend="session")
    open = MorphState(False)
    options = MorphState(())  # {id, name}

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return None

    @action(caps=())
    def choose(self, id: str = ""):
        self.current, self.open = id, False
        return [go("/" + id)]  # Host reloads workspace data
```

---

## 12. Version history + restore

```python
class Versions(Component):
    id = "versions"
    open = MorphState(False)
    items = MorphState(())  # {id, at, label}
    selected = MorphState("")

    @action(caps=())
    def show(self):
        self.open = True
        return None  # Host loads items

    @action(caps=())
    def select(self, id: str = ""):
        self.selected = id
        return None

    @action(caps=("docs.restore",))
    def restore(self):
        vid = self.selected
        self.open = False
        return [notify(f"Restored {vid}")]
```

---

## 13. Approval workflow

```python
class Approval(Component):
    id = "approval"
    status = MorphState("draft")  # draft|pending|approved|rejected
    comment = MorphState("")

    @action(caps=())
    def submit(self):
        self.status = "pending"
        return [notify("Submitted")]

    @action(caps=("approval.decide",))
    def approve(self):
        self.status = "approved"
        return [notify("Approved")]

    @action(caps=("approval.decide",))
    def reject(self, comment: str = ""):
        self.comment, self.status = comment, "rejected"
        return [notify("Rejected")]
```

---

## 14. Coupon / gift card

```python
class Coupon(Component):
    id = "coupon"
    code = MorphState("")
    applied = MorphState("")
    error = MorphState("")

    @action(caps=())
    def apply(self, code: str = ""):
        c = (code or self.code or "").strip().upper()
        # Host validates; on failure set error via apply_result
        self.code = c
        return None

    @action(caps=())
    def apply_result(self, ok: bool = False, code: str = "", message: str = ""):
        if ok:
            self.applied, self.error = code, ""
            return [notify("Coupon applied")]
        self.error = message or "Invalid"
        return None

    @action(caps=())
    def remove(self):
        self.applied, self.code, self.error = "", "", ""
        return None
```

Discount amounts stay on Host order model — not client plane.

---

## 15. KYC / capture steps

```python
class Kyc(Component):
    id = "kyc"
    step = MorphState(1, backend="store")  # 1 id 2 selfie 3 review
    status = MorphState("idle")

    @action(caps=())
    def next(self):
        self.step = min(3, int(self.step) + 1)
        return None

    @action(caps=())
    def submit(self):
        self.status = "pending_review"
        return [notify("Submitted for review")]
```

Upload binary stays Host; Behavior only steps/status.

---

## 16. Share sheet

```python
class Share(Component):
    id = "share"
    open = MorphState(False)
    url = MorphState("")

    @action(caps=())
    def open(self, url: str = ""):
        self.url, self.open = url, True
        return None

    @action(caps=())
    def close(self):
        self.open = False
        return None

    @action(caps=())
    def copied(self):
        return [notify("Link copied")]
```

---

## 17. Split pane resize

```python
class Split(Component):
    id = "split"
    ratio = MorphState(0.4, backend="client", key="ui.split.ratio")  # 0..1

    @action(caps=())
    def set_ratio(self, ratio: float = 0.4):
        r = max(0.15, min(0.85, float(ratio)))
        self.ratio = r
        return None
```

---

## 18–20. PDP variants, qty, stars

```python
class Pdp(Component):
    id = "pdp"
    color = MorphState("")
    size = MorphState("")
    qty = MorphState(1)
    rating = MorphState(0)  # user draft rating

    @action(caps=())
    def set_variant(self, color: str = "", size: str = ""):
        if color: self.color = color
        if size: self.size = size
        return None

    @action(caps=())
    def set_qty(self, qty: int = 1):
        self.qty = max(1, min(99, int(qty)))
        return None

    @action(caps=())
    def rate(self, stars: int = 0):
        self.rating = max(0, min(5, int(stars)))
        return None
```

---

## 21–22. Pin / watch

```python
class Watch(Component):
    id = "watch"
    on = MorphState(False)
    _pending = RefState(False)

    @action(caps=())
    def toggle(self):
        self.on = not bool(self.on)
        self._pending = True
        return None  # optimistic; Host confirm/rollback
```

---

## 23. Attachments list

```python
class Files(Component):
    id = "files"
    items = MorphState(())  # {id, name, pct, status}

    @action(caps=())
    def add(self, id: str = "", name: str = ""):
        self.items = tuple(self.items or ()) + ({{"id": id, "name": name, "pct": 0, "status": "uploading"}},)
        return None

    @action(caps=())
    def progress(self, id: str = "", pct: int = 0):
        self.items = tuple(
            {**x, "pct": pct} if x["id"] == id else x for x in (self.items or ())
        )
        return None

    @action(caps=())
    def remove(self, id: str = ""):
        self.items = tuple(x for x in (self.items or ()) if x["id"] != id)
        return None
```

---

## 24. Diff viewer tabs

```python
class Diff(Component):
    id = "diff"
    mode = MorphState("split")  # split|unified
    file = MorphState("")

    @action(caps=())
    def set_mode(self, mode: str = "split"):
        self.mode = mode
        return None

    @action(caps=())
    def select_file(self, file: str = ""):
        self.file = file
        return None
```

---

## 25. Timeline / vertical stepper

```python
class Timeline(Component):
    id = "timeline"
    active = MorphState(0)
    steps = MorphState(("Placed", "Shipped", "Delivered"))

    @action(caps=())
    def set_active(self, index: int = 0):
        self.active = max(0, int(index))
        return None
```

---

## 26–27. FAB menu + bottom nav

```python
class Fab(Component):
    id = "fab"
    open = MorphState(False)
    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return None

class BottomNav(Component):
    id = "bottomnav"
    tab = MorphState("home")
    @action(caps=())
    def select(self, tab: str = "home"):
        self.tab = tab
        return None
```

---

## 28–30. Auth wait, captcha gate, maintenance

```python
class MagicLink(Component):
    id = "magic"
    phase = MorphState("idle")  # idle|sent|error
    @action(caps=())
    def sent(self):
        self.phase = "sent"
        return None

class Challenge(Component):
    id = "challenge"
    open = MorphState(False)
    @action(caps=())
    def show(self):
        self.open = True
        return None
    @action(caps=())
    def pass_(self):
        self.open = False
        return None

class Maintenance(Component):
    id = "maint"
    on = MorphState(False)
    message = MorphState("")
    @action(caps=())
    def enable(self, message: str = "Read-only"):
        self.on, self.message = True, message
        return None
```

---

## How these nest into existing systems

| Residual | Nests into |
|----------|------------|
| Tree + preview | SaaS admin / docs |
| Lightbox | Commerce PDP, social |
| Map + panel | Booking, local commerce |
| Inline edit | Admin tables, docs |
| Tags | Admin, social compose |
| Date range | Admin filters, analytics |
| Tour | Any shell first-run |
| Offline queue | Mobile commerce / field apps |
| Tenant switcher | Multi-workspace SaaS |
| Versions | Docs / design tools |
| Approval | B2B admin |
| Coupon | Commerce checkout |
| KYC | Fintech onboarding |
| Share | Content, social |
| PDP variants | Commerce modal |
| FAB / bottom nav | Mobile shells |

## Still not Behavior

WebGL games, raw canvas editors, CRDT text internals, payment iframe PCI — Host embeds; Behavior only gates open/status.

With COMPLEX + COMPLEX_NESTED + this file, residual **interaction** cases used on mainstream global sites are covered.
