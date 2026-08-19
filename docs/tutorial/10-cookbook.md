# 10 — Cookbook

## Tabs (session Morph)

```python
tab = MorphState("overview")

@action(caps=())
def select_tab(self, tab: str = "overview"):
    self.tab = tab
    return None
```

## Wizard steps (store so refresh keeps progress)

```python
step = MorphState(1, backend="store")

@action(caps=())
def next_step(self):
    self.step = int(self.step) + 1
    return None
```

## One-shot toast without morph spam

Prefer `return [notify("Saved")]` instead of Morph flash fields.

## Draft autosave

```python
draft = MorphState("", backend="store")

@action(caps=())
def save_draft(self, text: str = ""):
    self.draft = text
    return None
```

## Silent request id

```python
req_id = RefState("")

@action(caps=())
def arm(self):
    import uuid
    self.req_id = str(uuid.uuid4())
    return None  # no morph
```

## Preview dry-run

```python
with app.preview():
    # session/store writes raise AuthorityError
    pass
```

## Inspect planes

```python
print(app.state.report)
print(app.state.backend("session").data)
```
