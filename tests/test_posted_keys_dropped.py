"""Posted keys the action does not name must not reach it.

A login-style ``**kwargs`` used to receive ``is_admin`` and ``role`` because
``bind_action_args`` forwarded ``VAR_KEYWORD``. Main drops those keys.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Login(Component):
    id = "login"
    seen = None

    def render(self):
        return "<form id='login'></form>"

    @action(caps=())
    def submit(self, email: str = "", password: str = "", **kwargs):
        self.seen = {
            "email": email,
            "password": password,
            "kwargs": dict(kwargs),
        }
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Login)
    return app


_POSTED = {
    "email": "ada@atelier.test",
    "password": "password12",
    "is_admin": True,
    "role": "admin",
}


def test_unnamed_posted_keys_do_not_reach_login():
    app = _app()
    app.dispatch("login.submit", **_POSTED)
    seen = app.get("login").seen
    assert seen["email"] == "ada@atelier.test"
    assert seen["password"] == "password12"
    assert seen["kwargs"] == {}

    app.submit("login.submit", dict(_POSTED))
    assert app.get("login").seen["kwargs"] == {}


async def test_async_unnamed_posted_keys_do_not_reach_login():
    app = _app()
    await app.async_dispatch("login.submit", **_POSTED)
    assert app.get("login").seen["kwargs"] == {}

    await app.async_submit("login.submit", dict(_POSTED))
    assert app.get("login").seen["email"] == "ada@atelier.test"
    assert app.get("login").seen["kwargs"] == {}
