# Wizard / stepper

```python
from ux_behavior import Component, MorphState, action, notify

class Onboarding(Component):
    id = "onboarding"
    step = MorphState(1, backend="store")  # survive refresh
    max_step = 3
    email = MorphState("")
    plan = MorphState("free")

    def render(self):
        s = int(self.step)
        return f"<div id='onboarding' data-step='{s}'>step {s}</div>"

    @action(caps=())
    def next(self):
        s = int(self.step)
        if s >= self.max_step:
            return [notify("Done")]
        if s == 1 and not str(self.email).strip():
            return [update("onboarding.email-error", "Email required")]
        self.step = s + 1
        return None

    @action(caps=())
    def back(self):
        self.step = max(1, int(self.step) - 1)
        return None

    @action(caps=())
    def goto(self, step: int = 1):
        self.step = min(self.max_step, max(1, int(step)))
        return None
```
