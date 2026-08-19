# 07 — Async actions

```python
from ux_behavior import Behavior, Component, MorphState, action

class Saver(Component):
    id = "saver"
    ok = MorphState(False)

    def render(self):
        return f"<div id='saver'>{self.ok}</div>"

    @action(caps=())
    async def save(self):
        # await db.commit()
        self.ok = True
        return None

app = Behavior.boot()
app.add(Saver)

# app.dispatch("saver.save")  # TypeError → use async_dispatch

import asyncio
ops = asyncio.run(app.async_dispatch("saver.save"))
assert app.get("saver").ok is True
```

Under ASGI + attach, the wire handler prefers **async** dispatch so both sync and async actions work.
