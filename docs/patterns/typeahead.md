# Search typeahead

```python
class SearchBox(Component):
    id = "search"
    query = MorphState("")
    open = MorphState(False)
    hits = MorphState(())  # tuple of {id, label}
    active = MorphState(0)

    def render(self):
        ...

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        self.open = bool(q)
        # Host injects search function
        self.hits = tuple(HOST_SEARCH(q)[:10])
        self.active = 0
        return None

    @action(caps=())
    def move(self, delta: int = 1):
        n = len(self.hits or ())
        if not n:
            return None
        self.active = (int(self.active) + int(delta)) % n
        return None

    @action(caps=())
    def choose(self, id: str = ""):
        self.open = False
        return [go(f"/items/{id}")]
```

Wire `app.use("search")` when Channel search drivers exist.
