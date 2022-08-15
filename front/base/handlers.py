from flask import render_template


def error_handler(e):
    return render_template("error.html", error=e)
