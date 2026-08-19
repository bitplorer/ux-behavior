# Tabs

## Single selection (session)

```python
from ux_behavior import Behavior, Component, MorphState, action

class ProductTabs(Component):
    id = "product.tabs"
    tab = MorphState("overview")  # overview | specs | reviews

    def render(self):
        t = self.tab
        def panel(name, body):
            show = "block" if t == name else "none"
            return f"<div role='tabpanel' style='display:{show}'>{body}</div>"
        return f"""
        <div id="product.tabs">
          <div role="tablist">
            <button data-tab="overview">Overview</button>
            <button data-tab="specs">Specs</button>
            <button data-tab="reviews">Reviews</button>
          </div>
          {panel("overview", "<p>Overview copy</p>")}
          {panel("specs", "<p>Spec table</p>")}
          {panel("reviews", "<p>Reviews list</p>")}
        </div>
        """

    @action(caps=())
    def select(self, tab: str = "overview"):
        allowed = {"overview", "specs", "reviews"}
        if tab not in allowed:
            return []  # ignore invalid
        self.tab = tab
        return None

app = Behavior.boot()
app.add(ProductTabs)
app.dispatch("product.tabs.select", tab="specs")
assert app.get("product.tabs").tab == "specs"
```

**Buttons:** `app.control(tabs.select, tab="reviews")`.

## Tabs + navigate (deep link)

```python
from ux_behavior import go

@action(caps=())
def select(self, tab: str = "overview"):
    self.tab = tab
    return [go(f"/product?tab={tab}")]
```

## Vertical / pill / controlled from parent

Same state. Parent action sets child via shared Behavior:

```python
app.get("product.tabs").tab = "reviews"  # or dispatch select
```

## Persist last tab across visits

```python
tab = MorphState("overview", backend="store")  # + Host store backend
```
