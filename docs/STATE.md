# State

## Author fields

| API | Effect |
|-----|--------|
| **MorphState** | may auto-morph (`useState`) |
| **RefState** | never auto-morph (`useRef`) |

```python
MorphState("home")                                 # session
MorphState(1, backend="store")
MorphState("system", backend="client", key="ui.theme")
MorphState(0, type=int)
MorphState("", validate=fn)
RefState(None)
UiState / PrefState / KeepState   # sugar
```

## Host storage — ``app.state``

```python
app.state.use("store", kv_backend)     # lock=True by default
app.state.use("session", b, lock=True)
app.state.report                       # {session, client, store} → memory|host|channel
app.state.locked
app.state.backends
app.state.reset("session")
app.state.reset()                      # all → memory
```

Attach installs Channel session/client only for **unlocked** planes (`lock=False`, `source="channel"`).

No ``set_plane_backend``. No SessionState/ClientState aliases.
