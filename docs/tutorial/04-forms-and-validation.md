# 04 — Forms and validation

## Typed arguments

```python
from ux_behavior import Behavior, Component, MorphState, action

class Profile(Component):
    id = "profile"
    name = MorphState("")

    def render(self):
        return f"<div id='profile'>{self.name}</div>"

    @action(caps=())
    def save(self, name: str = ""):
        self.name = name
        return None

app = Behavior.boot()
app.add(Profile)

# OK
app.dispatch("profile.save", name="Ada")

# Bad type → morph error target, no exception to Host
ops = app.dispatch("profile.save", name=123)  # type: ignore
assert ops[0].pair == ("ui.dom", "morph")
assert ops[0].payload["target"] == "profile.save.name-error"
```

## Field-level type=

```python
age = MorphState(0, type=int)
# inst.age = "1"  → TypeError (no coerce)
```

## submit helper

```python
app.submit("profile.save", {"name": "Ada"})
# same as dispatch with merged kwargs
```
