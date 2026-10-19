"""An unnamed posted key on an action with no ``**kwargs`` is a validation error.

The action does not run. ``is_admin`` and ``role`` never become attributes.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Login(Component):
    id = "login"
    seen = None

    def render(self):
        return "<form id='login'></form>"

    @action(caps=())
    def submit(self, email: str = "", password: str = ""):
        self.seen = (email, password)
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Login)
    return app


def test_unnamed_key_without_kwargs_is_a_validation_error():
    app = _app()
    ops = app.dispatch(
        "login.submit",
        email="ada@atelier.test",
        password="password12",
        is_admin=True,
        role="admin",
    )
    assert app.get("login").seen is None
    assert ops and ops[0].payload["target"] == "login.submit-error"
    assert "unexpected keyword" in ops[0].payload["patch"]
    assert "VALIDATION_FAILED" in app.diagnostics.summary()["codes"]


async def test_async_unnamed_key_without_kwargs_is_a_validation_error():
    app = _app()
    ops = await app.async_dispatch(
        "login.submit",
        email="ada@atelier.test",
        is_admin=True,
    )
    assert app.get("login").seen is None
    assert ops and "unexpected keyword" in ops[0].payload["patch"]
    assert "is_admin" in ops[0].payload["patch"]
