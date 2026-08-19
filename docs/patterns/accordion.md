# Accordion

## Single open

```python
open_id = MorphState("")  # section id or ""

@action(caps=())
def toggle(self, id: str = ""):
    self.open_id = "" if self.open_id == id else id
    return None
```

## Multi open

```python
open_ids = MorphState(())  # tuple[str]

@action(caps=())
def toggle(self, id: str = ""):
    s = set(self.open_ids or ())
    if id in s:
        s.remove(id)
    else:
        s.add(id)
    self.open_ids = tuple(sorted(s))
    return None
```
