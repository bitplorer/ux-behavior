"""Client plane write policy — refuse money-shaped paths."""

from __future__ import annotations

import re
from typing import Any

from ux_behavior.errors import AuthorityError

_RISKY = re.compile(
    r"(amount|price|qty|quantity|balance|money|cent|wallet|pay|cost|total|sku)",
    re.IGNORECASE,
)


def check_client_write(key: str, value: Any) -> None:
    path = str(key or "")
    if _RISKY.search(path):
        raise AuthorityError(
            f"client plane refuses money-shaped path {path!r}; "
            "use store/session or Host domain data"
        )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # numeric prefs are rare; still allow theme scale ints under safe keys
        if _RISKY.search(path):
            raise AuthorityError(
                f"client plane refuses numeric money-shaped write on {path!r}"
            )
