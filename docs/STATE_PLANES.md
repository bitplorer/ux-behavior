# State planes — claims == code (plane-aware)

## What they mean and do

| Marker | Plane | Storage key | Read/write |
|--------|-------|-------------|------------|
| `SessionState` | `session` | `{component.id}.{field}` | session backend |
| `ClientState` | `client` | `key=` or field name | client backend |
| `StoreState` | `store` | `{component.id}.{field}` | store backend |
| `TransientState` | *(none)* | instance only | `__dict__` only; **no dirty** |

Default backends: in-process ``MemoryPlanes`` on ``Behavior``.

## Host hooks

```python
app.set_plane_backend("session", my_backend)  # PlaneBackend: get/set
app.set_plane_backend("store", my_kv)
app.set_plane_backend("client", my_prefs)
```

## Binding

``Behavior.add`` calls ``component.bind_behavior(app)`` so fields find the root.

## Local mirror

Writes also update ``instance.__dict__`` so dirty projection and SSR still see values.

## Not claimed

Channel draft / browser client protocol until a Host installs those backends
(or wire attach soft-installs them with tests).
