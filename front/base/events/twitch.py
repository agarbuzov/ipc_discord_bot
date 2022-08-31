import settings

from uuid import UUID
from requests import Response

from flask import url_for

from models import session as db_session
from models import Broadcaster

from typing import Union
from typing import Tuple
from typing import Optional
from typing import Callable

from front.base.utils import twitch_api_request

from werkzeug import Response
from werkzeug import Request
from werkzeug.exceptions import BadRequest


class TwitchEvent:

    def __init__(self, request: Request) -> None:
        self._request = request
        self._type: Optional[str] = None
        self._action: Optional[Callable] = None
        self._result = None

    def execute(self) -> Union[Response, Tuple[str, int]]:
        self._define_type()
        self._define_action()
        self._action()
        return self._result

    def _define_type(self) -> None:
        self._type = self._request.headers.get("Twitch-Eventsub-Message-Type")
        if not self._type:
            raise BadRequest("Twitch-Eventsub-Message-Type header is missing on request")

    def _define_action(self) -> None:
        if self._type == "notification":
            self._action = self._handle_notification
        elif self._type == "webhook_callback_verification":
            self._action = self._handle_verification
        elif self._type == "revocation":
            self._action = self._handle_revocation
        else:
            raise BadRequest("Unknown event type")

    def _handle_notification(self):
        pass

    def _handle_verification(self) -> None:
        challenge = self._request.json.get("challenge")
        self._result = Response(challenge, mimetype="text/plain")

    def _handle_revocation(self):
        pass


class TwitchSubscriptionCreate:

    def __init__(self, event_type, version="1") -> None:
        self._type: str = event_type
        self._version: str = version
        self._condition: Optional[dict] = None
        self._data: Optional[dict] = None
        self._response: Optional[dict] = None

    def execute(self):
        self._build_request_data()
        self._execute_request()

    def _build_request_data(self) -> None:
        self._data = {
            "type": self._type,
            "version": self._version,
            "condition": self._condition,
            "transport": {
                "method": "webhook",
                "callback": url_for("event_handler", platform="twitch", _external=True),
                "secret": settings.SECRET_KEY
            }
        }

    def _execute_request(self) -> None:
        self._response = twitch_api_request(
            "post", "/eventsub/subscriptions", 202, json=self._data
        )


class TwitchSubscriptionDelete:

    def __init__(self, event_id) -> None:
        self._event_id: UUID = event_id

    def execute(self):
        self._execute_reqeuest()

    def _execute_reqeuest(self):
        self._response = twitch_api_request(
            "delete", "/eventsub/subscriptions", 204, params={"id": self._event_id}
        )


class UserUpdate(TwitchEvent):

    def __init__(self, request) -> None:
        super().__init__(request)

    def _handle_notification(self) -> None:
        broadcaster_data = self._request.json.get("event", {})
        broadcaster = db_session.query(Broadcaster).get(broadcaster_data.get("user_id"))
        broadcaster.login = broadcaster_data.get("user_login")
        broadcaster.name = broadcaster_data.get("user_name")
        db_session.add(broadcaster)
        db_session.commit()
        self._result = ("", 204)

    def _handle_revocation(self) -> None:
        identifier = self._request.json.get("subscription", {}).get("id")
        broadcaster = db_session.query(Broadcaster).filter_by(identifier=identifier)
        broadcaster.identifier = None
        db_session.add(broadcaster)
        db_session.commit()
        self._result = ("", 204)
