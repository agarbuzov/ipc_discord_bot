from flask import url_for
from flask import session
from flask import request
from flask import redirect
from flask import render_template
from flask.views import MethodView

from models import session as db_session
from models import Alert

from front.base.decorators import token_required

from front.alerts.events.twitch import UserUpdateCreate
from front.alerts.events.twitch import UserUpdateDelete
from front.alerts.events.twitch import StreamOnlineCreate
from front.alerts.events.twitch import StreamOnlineDelete

from werkzeug.exceptions import BadRequest


class AlertsIndex(MethodView):

    @staticmethod
    @token_required
    def get():
        alerts = db_session.query(Alert).filter_by(creator_id=session.user.id).all()
        return render_template("alerts/index.html", alerts=alerts)


class AlertsCreate(MethodView):

    def __init__(self) -> None:
        self.platform = request.form.get("platform")

    @token_required
    def post(self):
        if self.platform == "twitch":
            UserUpdateCreate(request).execute()
            StreamOnlineCreate(request).execute()
        else:
            raise BadRequest("Unsupported platform")
        return redirect(url_for("alerts.index"))


class AlertsDelete(MethodView):

    def __init__(self) -> None:
        self.platform = request.form.get("platform")

    @token_required
    def post(self):
        if self.platform == "twitch":
            # UserUpdateDelete(request).execute()
            StreamOnlineDelete(request).execute()
        else:
            raise BadRequest("Unsupported platform")
        return redirect(url_for("alerts.index"))
