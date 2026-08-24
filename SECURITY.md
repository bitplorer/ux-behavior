# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes |
| < 0.3   | Upgrade |

## Threat model

**ux-behavior owns product meaning → verified `list[Op]`.** Live Cap crypto is **ux-channel**. This layer enforces Cap Law at dispatch and fail-closed `AuthorityError` when Channel is not attached.

| In scope | Out of scope |
|----------|----------------|
| `@action(caps=...)` empty = public | Cap crypto, JTI, wire codecs |
| `strict_caps=True` + `AuthorityError` | HTML / XSS (`ux-dom`) |
| Isolation Law | Motion IR |
| Validation errors | HTTP / ASGI authn |

`Behavior.trust()` is a **test-only** door. Do not use it in product code.

## Reporting

GitHub Security Advisory on [bitplorer/ux-behavior](https://github.com/bitplorer/ux-behavior/security/advisories/new) or **bitplorer@outlook.com** (`ux-behavior security`). Do not file a public issue for unreleased details. Acknowledge within 5 business days.
