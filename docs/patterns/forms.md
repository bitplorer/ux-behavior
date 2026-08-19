# Forms

## Controlled fields + field errors

```python
from ux_behavior import Component, MorphState, action, submit_outcome, update

class ProfileForm(Component):
    id = "profile.form"
    name = MorphState("")
    email = MorphState("")

    def render(self):
        return f"""
        <form id="profile.form">
          <input name="name" value="{self.name}"/>
          <input name="email" value="{self.email}"/>
        </form>"""

    @action(caps=())
    def save(self, name: str = "", email: str = ""):
        ops = []
        if not name.strip():
            ops.append(update("profile.form.name-error", "Required"))
        if "@" not in email:
            ops.append(update("profile.form.email-error", "Invalid email"))
        if ops:
            return ops
        self.name = name.strip()
        self.email = email.strip()
        return submit_outcome(
            "profile.form",
            self.render(),
            message="Profile saved",
        )
```

## Dirty guard (leave form)

```python
dirty = MorphState(False)

@action(caps=())
def edit(self, name: str = ""):
    self.name = name
    self.dirty = True
    return None
```

Pair with confirm modal when `dirty` and navigate.
