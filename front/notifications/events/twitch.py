from models import session as db_session
from models import Notification

from front.base.utils import send_socket_message
from front.base.events.twitch import TwitchEvent


class StreamOnline(TwitchEvent):

    def __init__(self, request) -> None:
        super().__init__(request)

    def _handle_notification(self) -> None:
        broadcaster_id = self._request.json.get("event", {}).get("broadcaster_user_id")
        send_socket_message("send_notification", {"broadcaster_id": broadcaster_id})
        self._result = ("", 204)

    def _handle_revocation(self) -> None:
        identifier = self._request.json.get("subscription", {}).get("id")
        db_session.query(Notification).filter_by(identifier=identifier).delete()
        db_session.commit()
        self._result = ("", 204)
