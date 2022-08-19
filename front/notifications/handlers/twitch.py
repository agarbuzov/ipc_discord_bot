import settings

from requests import Response

from flask import session
from flask import url_for
from flask import redirect

from sqlalchemy import and_

from models import session as db_session
from models import Notification

from typing import Union
from typing import Tuple
from typing import Optional
from typing import Callable

from front.base.utils import send_socket_message
from front.notifications.utils import twitch_api_request

from werkzeug import Response
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import BadRequest


class TwitchEventReceive:

    def __init__(self, request) -> None:
        self._request = request
        self._type: Optional[str] = None
        self._action: Optional[Callable] = None
        self._result = None

    def execute(self) -> Union[Response, Tuple[str, int]]:
        self._define_type()
        self._process_action()
        self._action()
        return self._result

    def _process_action(self) -> None:
        if self._type == "notification":
            self._action = self._process_notification
        elif self._type == "webhook_callback_verification":
            self._action = self._process_verification
        elif self._type == "revocation":
            self._action = self._process_revocation
        else:
            raise BadRequest("Unknown event type")

    def _define_type(self) -> None:
        self._type = self._request.headers.get("Twitch-Eventsub-Message-Type")
        if not self._type:
            raise BadRequest("Twitch-Eventsub-Message-Type header is missing on request")

    def _process_notification(self) -> None:
        broadcaster_id = self._request.json.get("event", {}).get("broadcaster_user_id")
        send_socket_message({"event": "send_notification", "data": {"broadcaster_id": broadcaster_id}})
        self._result = ("", 204)

    def _process_verification(self) -> None:
        challenge = self._request.json.get("challenge")
        self._result = Response(challenge, mimetype="text/plain")

    def _process_revocation(self) -> None:
        identifier = self._request.json.get("subscription", {}).get("id")
        db_session.query(Notification).filter_by(identifier=identifier).delete()
        db_session.commit()
        self._request = ("", 204)


class TwitchEventCreate:

    def __init__(self, request) -> None:
        self._platform: str = "twitch"
        self._body = request.form.get("body")
        self._guild: int = request.form.get("guild")
        self._channel: int = request.form.get("channel")
        self._broadcaster: str = request.form.get("broadcaster")
        self._creator_id: Optional[int] = session.user.id
        self._data: Optional[dict] = None
        self._response: Optional[dict] = None
        self._broadcaster_id: Optional[int] = None

    def execute(self) -> Response:
        self._get_broadcaster_id()
        self._build_request()
        self._execute_request()
        self._save_record()
        return redirect(url_for("notifications.index"))

    def _get_broadcaster_id(self) -> None:
        data = {"login": self._broadcaster}
        response = twitch_api_request(
            "get", "/users/", params=data
        )
        broadcaster_id = response.get("data", [{}])[0].get("id")
        if not broadcaster_id:
            raise NotFound("Twitch user with such nickname not found")
        self._broadcaster_id = broadcaster_id

    def _build_request(self) -> None:
        self._data = {
            "type": "stream.online",
            "version": "1",
            "condition": {
                "broadcaster_user_id": self._broadcaster_id
            },
            "transport": {
                "method": "webhook",
                "callback": url_for("notifications.receive", platform="twitch", _external=True),
                "secret": settings.SECRET_KEY
            }
        }

    def _execute_request(self) -> None:
        self._response = twitch_api_request(
            "post", "/eventsub/subscriptions", 202, json=self._data
        )

    def _save_record(self) -> None:
        notification_id = self._response.get("data", [{}])[0].get("id")
        if not notification_id:
            raise BadRequest("ID is missing on request body")
        notification = Notification(
            identifier=notification_id,
            platform=self._platform,
            guild_id=self._guild,
            channel_id=self._channel,
            broadcaster_id=self._broadcaster_id,
            body=self._body,
            creator_id=self._creator_id
        )
        db_session.add(notification)
        db_session.commit()


class TwitchEventDelete:

    def __init__(self, request) -> None:
        self._id: int = request.form.get("id")
        self._data: Optional[dict] = None
        self._creator_id: Optional[int] = session.user.id

    def execute(self) -> Response:
        self._check_user()
        self._build_request()
        self._execute_request()
        return redirect(url_for("notifications.index"))

    def _build_request(self) -> None:
        self._data = {
            "id": self._id
        }

    def _check_user(self) -> None:
        record = db_session.query(Notification).filter(
            and_(Notification.identifier == self._id, Notification.creator_id == self._creator_id)
        ).delete()

        if not record:
            raise NotFound

        db_session.commit()

    def _execute_request(self) -> None:
        self._response = twitch_api_request(
            "delete", "/eventsub/subscriptions", 204, params=self._data
        )
