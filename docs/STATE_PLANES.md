# State planes

## Offline (always)

| Marker | Backend | Dirty |
|--------|---------|-------|
| SessionState | MemoryPlanes.session | yes |
| ClientState | MemoryPlanes.client | **no** |
| StoreState | MemoryPlanes.store | yes |
| TransientState | instance only | **no** |

## Live attach (opt-in default)

```python
app.attach(asgi)                      # channel_planes=True by default
app.attach(asgi, channel_planes=False)  # keep memory only
```

On successful Channel boot, **unlocked** planes get sensible defaults:

| Plane | Auto backend |
|-------|----------------|
| session | Channel `st.session(key)` |
| client | Channel `st.client.set` + mirror |
| store | stays memory (Host plugs kv if needed) |

**Host wins:**

```python
app.set_plane_backend("session", my_backend)  # locks plane
app.attach(asgi)  # will not overwrite session
```

**Fail-closed:** import/API errors leave memory bags; never raise into product.

See `attach_info(app)["planes"]` for `channel` | `skipped_host` | `skipped_error` | `memory`.
