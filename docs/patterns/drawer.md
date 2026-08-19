# Drawer / sheet

Same structure as modal: `open: MorphState(bool)` + `show`/`hide`.

```python
class CartDrawer(Component):
    id = "drawer.cart"
    open = MorphState(False)

    def render(self):
        cls = "drawer open" if self.open else "drawer"
        return f"<aside id='drawer.cart' class='{cls}'>...</aside>"

    @action(caps=())
    def show(self):
        self.open = True
        return None

    @action(caps=())
    def hide(self):
        self.open = False
        return None
```

Often paired with `Cart` component: add item → optional `drawer.cart.show`.
