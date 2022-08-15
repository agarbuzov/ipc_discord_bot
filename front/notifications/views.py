import settings

from flask import url_for
from flask import session
from flask import jsonify
from flask import request
from flask import render_template
from flask.views import MethodView
from flask import Response

from models import session as db_session
from models import Notification

from front.base.decorators import token_required
from front.notifications.utils import twitch_api_request


class NotificationsIndex(MethodView):

    @staticmethod
    @token_required
    def get():
        return render_template("notifications/index.html")


class NotificationsCreate(MethodView):

    def __init__(self) -> None:
        self.platform = request.form.get("platform")
        self.guild = request.form.get("guild")
        self.channel = request.form.get("channel")
        self.body = request.form.get("body")
        self.broadcaster = request.form.get("broadcaster")

    @staticmethod
    @token_required
    def get():
        return render_template("notifications/create.html")

    @token_required
    def post(self):
        match self.platform:
            case "twitch":
                response = self.twitch_notif_create()
            case "trovo":
                pass
            case "telegram":
                pass
        return jsonify(response)

    def twitch_notif_create(self):
        url = "/eventsub/subscriptions"
        data = {
            "type": "stream.online",
            "version": "1",
            "condition": {
                "broadcaster_user_id": self.broadcaster
            },
            "transport": {
                "method": "webhook",
                "callback": url_for("notifications.receive", platform="twitch", _external=True, _scheme="https"),
                "secret": settings.SECRET_KEY
            }
        }
        response = twitch_api_request("post", url, 202, json=data)
        notification_id = response.get("data")[0].get("id")
        notification = Notification(
            identifier=notification_id,
            platform=self.platform,
            guild_id=int(self.guild),
            channel_id=int(self.channel),
            broadcaster_id=int(self.broadcaster),
            body=self.body,
            creator_id=session.user.id
        )
        db_session.add(notification)
        db_session.commit()
        return response


class NotificationsDelete(MethodView):

    def __init__(self):
        self.platform = request.form.get("platform")
        self.user_id = session.user.id


class NotificationsReceive(MethodView):

    @staticmethod
    def post(platform):
        if challenge := request.json.get("challenge"):
            return Response(challenge, mimetype="text/plain")
        return "", 200
