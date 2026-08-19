# Nested chrome (modal + tabs, drawer + filters)

Use **stable nested ids**:

```text
modal.product
modal.product.tabs
drawer.filters
```

Each Component owns its Morph flags. Parent `show` does not reset child tab unless you dispatch child `select`.

```python
@action(caps=())
def open_product(self, id: str = ""):
    self.product_id = id
    self.open = True
    # optional: reset tabs
    # return via Host calling app.dispatch("modal.product.tabs.select", tab="overview")
    return None
```

**Z-index / focus** remain CSS/Host JS concerns.
