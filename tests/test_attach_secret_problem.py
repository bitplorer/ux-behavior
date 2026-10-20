"""attach_secret_problem(env) answers, before boot, whether attach() refuses the secret.

One implementation: attach() raises with the message this function returns.
The length rules belong to ux-channel; these tests never restate them.
"""

from __future__ import annotations

import importlib.util

import pytest

import ux_behavior.wire as wire
from ux_behavior import Behavior
from ux_behavior.wire import attach_secret_problem

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
needs_channel = pytest.mark.skipif(not HAS_CHANNEL, reason="ux-channel not installed")

PUBLIC_DEV = "dev-secret-key-32chars-minimum!!!!"
STRONG = "s" * 48
SECRET_VARS = ("UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL", "DEBUG")

# (id, env, problem expected). Policy refusals need no ux-channel.
POLICY_REFUSED = [
    ("missing", {}),
    ("missing-debug-empty", {"DEBUG": ""}),
    ("missing-debug-0", {"DEBUG": "0"}),
    ("missing-debug-false", {"DEBUG": "false"}),
    ("missing-debug-y", {"DEBUG": "y"}),
    ("missing-debug-enabled", {"DEBUG": "enabled"}),
    ("dev-denylist", {"UX_CHANNEL_SECRET": PUBLIC_DEV}),
    ("dev-denylist-behavior-var", {"UX_BEHAVIOR_SECRET": PUBLIC_DEV}),
    ("dev-denylist-debug", {"UX_CHANNEL_SECRET": PUBLIC_DEV, "DEBUG": "1"}),
    ("redis-no-secret", {"REDIS_URL": "redis://localhost:6379/0"}),
    ("redis-no-secret-debug", {"REDIS_URL": "redis://localhost:6379/0", "DEBUG": "1"}),
    ("redis-no-secret-debug-on", {"REDIS_URL": "redis://x", "DEBUG": " ON "}),
]
# Refused only by ux-channel's own validators.
LENGTH_REFUSED = [
    ("short-1", {"UX_CHANNEL_SECRET": "x"}),
    ("short-7", {"UX_CHANNEL_SECRET": "a" * 7}),
    ("short-8", {"UX_CHANNEL_SECRET": "a" * 8}),
    ("short-15", {"UX_CHANNEL_SECRET": "a" * 15}),
    ("short-15-debug", {"UX_CHANNEL_SECRET": "a" * 15, "DEBUG": "1"}),
    ("short-15-behavior-var", {"UX_BEHAVIOR_SECRET": "a" * 15}),
    ("short-redis", {"UX_CHANNEL_SECRET": "a" * 20, "REDIS_URL": "redis://x"}),
]
ACCEPTED = [
    ("strong", {"UX_CHANNEL_SECRET": STRONG}),
    ("strong-behavior-var", {"UX_BEHAVIOR_SECRET": STRONG}),
    ("strong-16", {"UX_CHANNEL_SECRET": "a" * 16}),
    ("debug-1", {"DEBUG": "1"}),
    ("debug-true", {"DEBUG": "true"}),
    ("debug-yes-padded", {"DEBUG": " Yes "}),
    ("debug-on", {"DEBUG": "on"}),
    ("strong-debug-0", {"UX_CHANNEL_SECRET": STRONG, "DEBUG": "0"}),
    ("channel-var-wins", {"UX_CHANNEL_SECRET": STRONG, "UX_BEHAVIOR_SECRET": "x"}),
]
ALL_CASES = (
    [(i, e, True) for i, e in POLICY_REFUSED]
    + [(i, e, True) for i, e in LENGTH_REFUSED]
    + [(i, e, False) for i, e in ACCEPTED]
)


def _ids(cases):
    return [c[0] for c in cases]


def test_name_is_on_the_wire_door():
    assert "attach_secret_problem" in wire.__all__
    assert wire.attach_secret_problem is attach_secret_problem


@pytest.mark.parametrize(("case", "env"), POLICY_REFUSED, ids=_ids(POLICY_REFUSED))
def test_policy_refusal_returns_message(case: str, env: dict[str, str]):
    problem = attach_secret_problem(env)
    assert isinstance(problem, str) and problem


def test_messages_name_the_rule():
    assert "public dev secret" in attach_secret_problem({"UX_CHANNEL_SECRET": PUBLIC_DEV})
    assert "REDIS_URL" in attach_secret_problem({"REDIS_URL": "redis://x", "DEBUG": "1"})
    assert "UX_CHANNEL_SECRET" in attach_secret_problem({})


def test_explicit_secret_overrides_env():
    assert attach_secret_problem({}, secret=PUBLIC_DEV) is not None
    if HAS_CHANNEL:
        assert attach_secret_problem({}, secret=STRONG) is None


def test_env_mapping_ignores_process_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("UX_CHANNEL_SECRET", STRONG)
    assert attach_secret_problem({}) is not None


def test_default_reads_process_env(monkeypatch: pytest.MonkeyPatch):
    for name in SECRET_VARS:
        monkeypatch.delenv(name, raising=False)
    assert attach_secret_problem() is not None
    monkeypatch.setenv("UX_CHANNEL_SECRET", PUBLIC_DEV)
    assert "public dev secret" in attach_secret_problem()


@pytest.mark.skipif(HAS_CHANNEL, reason="ux-channel installed")
def test_without_channel_secret_is_not_accepted():
    problem = attach_secret_problem({"UX_CHANNEL_SECRET": STRONG})
    assert problem and "ux_channel" in problem


@needs_channel
@pytest.mark.parametrize(("case", "env"), LENGTH_REFUSED, ids=_ids(LENGTH_REFUSED))
def test_length_refusal_carries_ux_channel_message(case: str, env: dict[str, str]):
    problem = attach_secret_problem(env)
    assert isinstance(problem, str) and problem
    assert "ux_channel" in problem


@needs_channel
@pytest.mark.parametrize(("case", "env"), ACCEPTED, ids=_ids(ACCEPTED))
def test_accepted_returns_none(case: str, env: dict[str, str]):
    assert attach_secret_problem(env) is None


@needs_channel
@pytest.mark.parametrize(("case", "env", "refused"), ALL_CASES, ids=_ids(ALL_CASES))
def test_attach_refuses_exactly_when_problem(
    monkeypatch: pytest.MonkeyPatch, case: str, env: dict[str, str], refused: bool
):
    fastapi = pytest.importorskip("fastapi")
    if "REDIS_URL" in env and not refused:
        pytest.skip("accepted REDIS_URL config needs a live Redis")
    for name in SECRET_VARS:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    problem = attach_secret_problem()
    assert (problem is not None) is refused

    app = Behavior.boot(strict_attach=True)
    if refused:
        with pytest.raises(RuntimeError) as info:
            app.attach(fastapi.FastAPI())
        assert str(info.value) == problem
        codes = [e.code for e in app.diagnostics.events if e.level == "error"]
        assert codes == ["ATTACH_SECRET_REQUIRED"]
    else:
        assert app.attach(fastapi.FastAPI()) is not None
