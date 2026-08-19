# Pagination & load more

```python
page = MorphState(1)
page_size = MorphState(20)
total = MorphState(0)  # Host fills

@action(caps=())
def set_page(self, page: int = 1):
    self.page = max(1, int(page))
    return None  # Host render uses page to slice query

@action(caps=())
def more(self):
    self.page = int(self.page) + 1
    return None
```

Infinite scroll: browser intersection observer → `list.more`.
