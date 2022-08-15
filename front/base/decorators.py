from flask import session
from flask import url_for
from flask import redirect


def token_required(func):
    def inner(*args, **kwargs):
        if not session.get("token"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return inner
