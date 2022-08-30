from typing import Type
from typing import Optional

from front.base.events.twitch import TwitchEvent
from front.base.events.twitch import UserUpdate
from front.notifications.events.twitch import StreamOnline

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
        self._define_type()
        self._define_handler()
        return self._handler(self._request).execute()

    def _define_type(self) -> None:
        self._type = self._request.headers.get("Twitch-Eventsub-Subscription-Type")
        if not self._type:
            raise BadRequest("Twitch-Eventsub-Subscription-Type header is missing on request")

    def _define_handler(self):
        self._handler = self._event_handlers.get(self._type, TwitchEvent)
