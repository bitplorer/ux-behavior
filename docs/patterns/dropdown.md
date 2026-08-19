# Dropdown / menu

## Open / close / choose

```python
from ux_behavior import Behavior, Component, MorphState, action

class AccountMenu(Component):
    id = "account.menu"
    open = MorphState(False)
    value = MorphState("")  # last chosen

    def render(self):
        o = "true" if self.open else "false"
        panel = ""
        if self.open:
            panel = """
            <ul role="menu">
              <li><button data-v="profile">Profile</button></li>
              <li><button data-v="billing">Billing</button></li>
              <li><button data-v="logout">Log out</button></li>
            </ul>"""
        return f"""
        <div id="account.menu" data-open="{o}">
          <button aria-expanded="{o}">Account</button>
          {panel}
        </div>"""

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return None

    @action(caps=())
    def close(self):
        self.open = False
        return None

    @action(caps=())
    def choose(self, v: str = ""):
        self.value = v
        self.open = False
        return None
```

## Click-outside

Browser posts `account.menu.close` (Host listener). No special library support required.

## Combobox (query + list)

```python
query = MorphState("")
open = MorphState(False)
hits = MorphState(())  # tuple[str]

@action(caps=())
def type(self, q: str = ""):
    self.query = q
    self.open = True
    self.hits = tuple(x for x in HOST_INDEX if q.lower() in x.lower())[:8]
    return None

@action(caps=())
def choose(self, v: str = ""):
    self.value = v
    self.query = v
    self.open = False
    return None
```

Debounce typing in the browser; still one `type` action per committed query.
