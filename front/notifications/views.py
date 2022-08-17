from flask import session
from flask import request
from flask import render_template
from flask.views import MethodView

from models import session as db_session
from models import Notification

from front.base.decorators import token_required

from front.notifications.handlers.twitch import TwitchEventCreate
from front.notifications.handlers.twitch import TwitchEventReceive

from werkzeug.exceptions import BadRequest


class NotificationsIndex(MethodView):

    @staticmethod
    @token_required
    def get():
        notifications = db_session.query(Notification).all()
        return render_template("notifications/index.html", notifications=notifications)


class NotificationsCreate(MethodView):

    def __init__(self) -> None:
        self.platform = request.form.get("platform")

    @token_required
    def post(self):
        if self.platform == "twitch":
            response = TwitchEventCreate(request).execute()
        else:
            raise BadRequest("Unsupported platform")
        return response


class NotificationsDelete(MethodView):

    def __init__(self):
        self.platform = request.form.get("platform")
        self.user_id = session.user.id

    def post(self):
        return "", 200


class NotificationsReceive(MethodView):

    @staticmethod
    def post(platform):
        if platform == "twitch":
            response = TwitchEventReceive(request).execute()
        else:
            raise BadRequest("Unsupported platform")
        return response
