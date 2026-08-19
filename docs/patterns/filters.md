# Filters & sort

```python
from ux_behavior import Component, MorphState, action

class CatalogFilters(Component):
    id = "catalog.filters"
    q = MorphState("")
    category = MorphState("all")
    sort = MorphState("popular")  # popular|price|new
    dir = MorphState("desc")

    def render(self):
        return f"<form id='catalog.filters' data-q='{self.q}'></form>"

    @action(caps=())
    def set(self, q: str = "", category: str = "all", sort: str = "popular", dir: str = "desc"):
        self.q = q
        self.category = category
        self.sort = sort
        self.dir = dir
        return None

    @action(caps=())
    def clear(self):
        self.q = ""
        self.category = "all"
        self.sort = "popular"
        self.dir = "desc"
        return None
```

Host list component reads the same Behavior fields or receives filter snapshot via dispatch args.
