from flask import session
from flask import render_template


def error_handler(e):
    if not session.get("token"):
        return e
    return render_template("error.html", error=e)
