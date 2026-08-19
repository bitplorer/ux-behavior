"""Local Cap mint/verify — Host-free authority for offline + tests.

When Channel is attached, live requests should still verify at the edge;
this machine seals control() and submit()/dispatch(cap=...) without Host code.
Does not import ux_channel.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any


class CapError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def hash_args(args: dict[str, Any]) -> str:
    blob = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


@dataclass
class OnceStore:
    _seen: set[str] = field(default_factory=set)

    def consume(self, cap_id: str) -> None:
        if cap_id in self._seen:
            raise CapError("cap already consumed")
        self._seen.add(cap_id)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


class CapMachine:
    def __init__(self, secret: str | None = None, *, max_age: int = 3600) -> None:
        self.secret = (
            secret
            or os.environ.get("UX_BEHAVIOR_SECRET")
            or os.environ.get("UX_CHANNEL_SECRET")
            or "dev-secret-key-32chars-minimum!!!!"
        ).encode("utf-8")
        self.max_age = max_age
        self.once = OnceStore()
        self._seq = 0

    def mint(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        once: bool = True,
        ttl: int | None = None,
    ) -> str:
        self._seq += 1
        payload = {
            "id": f"c{self._seq:08d}",
            "exp": int(time.time()) + int(ttl or self.max_age),
            "action": action,
            "digest": hash_args(dict(args or {})),
            "once": int(bool(once)),
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sig = hmac.new(self.secret, body, hashlib.sha256).hexdigest()[:32]
        return f"{_b64(body)}.{sig}"

    def verify(
        self, token: str | None, action: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        if not token:
            raise CapError("cap missing")
        if "." not in token:
            raise CapError("cap malformed")
        blob, sig = token.rsplit(".", 1)
        try:
            body = _unb64(blob)
        except Exception as exc:
            raise CapError("cap malformed") from exc
        expect = hmac.new(self.secret, body, hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(expect, sig):
            raise CapError("cap signature")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise CapError("cap malformed") from exp
        try:
            exp = int(payload["exp"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CapError("cap expiry") from exp
        if exp < int(time.time()):
            raise CapError("cap expired")
        if payload.get("action") != action:
            raise CapError("cap action mismatch")
        if payload.get("digest") != hash_args(args):
            raise CapError("cap args mismatch")
        cap_id = str(payload.get("id") or "")
        if payload.get("once") in {1, "1", True}:
            self.once.consume(cap_id)
        return {"id": cap_id, "action": action, "exp": exp}
