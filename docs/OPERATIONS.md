# Operations

## Boot profiles

### Production

```python
app = Behavior.boot(
    "prod",
    strict_caps=True,
    client_risk=True,
    strict_control=True,
    strict_attach=True,
)
app.state.use("store", redis_backed, lock=True)
app.attach(asgi)  # must succeed
```

### CI / unit tests

```python
app = Behavior.boot("test")
# public actions only, or:
with app.trust():
    app.dispatch("secure.act")
```

### Local offline UI experiments

```python
app = Behavior.boot("dev", strict_control=False)
# control() may emit offline attrs; watch diagnostics
```

## Observability

- Log `app.diagnostics.summary()` on request failure.
- Metric counters: map diagnostic `code` strings.
- `app.state.report` for plane source drift (`memory` vs `channel`).

## Doctor

```bash
uxbehavior doctor --fail
```

Checks: frozen public surface, stamp hygiene, banned imports outside wire, banned tokens.

## Testing checklist

1. Public action morph / no-op Ref  
2. Protected action raises offline  
3. Validation morph targets  
4. Continuation emit  
5. async_dispatch  
6. preview blocks session write  
7. client risk on price key  
8. stamp reject  
9. doctor clean  
