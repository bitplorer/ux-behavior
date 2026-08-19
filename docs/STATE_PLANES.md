# State planes

## Dirty policy (ux-behavior)

**Dirty = “re-render this component for SSR morph”** when an action returns `None`.

| Marker | Dirty? | Why |
|--------|--------|-----|
| SessionState | **yes** | UI chrome is painted server-side |
| ClientState | **yes** | Prefs may be baked into SSR HTML (`class`, theme); morph must refresh |
| StoreState | **yes** | Component data drives render |
| TransientState | **no** | Ephemeral; must not request morph alone |

> Note: ux-app skipped dirty on client because it leaned on browser client ops.
> ux-behavior is **SSR-first**, so ClientState stays dirty-able. Live `st.client.set`
> can still enqueue browser ops in parallel.

## Offline backends

| Marker | Backend |
|--------|---------|
| SessionState | MemoryPlanes.session |
| ClientState | MemoryPlanes.client |
| StoreState | MemoryPlanes.store |
| TransientState | instance only |

## Live attach (opt-in default)

```python
app.attach(asgi)                       # channel_planes=True
app.attach(asgi, channel_planes=False) # memory only
app.set_plane_backend("session", b)    # Host locks; attach will not overwrite
```

| Plane | Auto on attach |
|-------|----------------|
| session | Channel `st.session` |
| client | Channel `st.client` + mirror |
| store | memory (Host plugs kv) |

Fail-closed: errors leave memory. See `attach_info(app)["planes"]`.
