import hmac
import hashlib

from typing import Type
from typing import Optional

import settings
from front.base.events.twitch import TwitchEvent
from front.base.events.twitch import UserUpdate
from front.notifications.events.twitch import StreamOnline

from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import BadRequest


class TwitchEventHandler:
    _event_handlers = {
        "stream.online": StreamOnline,
        "user.update": UserUpdate,
    }

    def __init__(self, request) -> None:
        self._request = request
        self._type: Optional[str] = None
        self._handler: Optional[Type[TwitchEvent]] = None
        self._result = None

    def execute(self):
        self._verify_event()
        self._define_type()
        self._define_handler()
        return self._handler(self._request).execute()

    def _verify_event(self):
        body = self._request.data
        event_id = self._request.headers.get("Twitch-Eventsub-Message-Id").encode()
        timestamp = self._request.headers.get("Twitch-Eventsub-Message-Timestamp").encode()
        event_signature = self._request.headers.get("Twitch-Eventsub-Message-Signature")[7:]
        signature = hmac.new(settings.SECRET_KEY.encode(), event_id+timestamp+body, hashlib.sha256).hexdigest()
        if event_signature != signature:
            raise Forbidden("Verification failed")

    def _define_type(self) -> None:
        self._type = self._request.headers.get("Twitch-Eventsub-Subscription-Type")
        if not self._type:
            raise BadRequest("Twitch-Eventsub-Subscription-Type header is missing on request")

    def _define_handler(self):
        self._handler = self._event_handlers.get(self._type, TwitchEvent)
