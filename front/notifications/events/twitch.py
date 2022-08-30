from typing import Optional

from flask import session

from models import session as db_session
from models import Notification
from models import Broadcaster

from front.base.utils import twitch_api_request
from front.base.utils import send_socket_message
from front.base.events.twitch import TwitchEvent
from front.base.events.twitch import TwitchSubscribeDelete
from front.base.events.twitch import TwitchSubscribeCreate

from werkzeug.exceptions import NotFound


class StreamOnline(TwitchEvent):

    def __init__(self, request) -> None:
        super().__init__(request)

    def _handle_notification(self) -> None:
        broadcaster_id = self._request.json.get("event", {}).get("broadcaster_user_id")
        send_socket_message("send_notification", {"broadcaster_id": broadcaster_id})
        self._result = ("", 204)

    def _handle_revocation(self) -> None:
        identifier = self._request.json.get("subscription", {}).get("id")
        notification = db_session.query(Notification).filter_by(identifier=identifier)
        broadcaster = notification.broadcaster
        self._response = twitch_api_request(
            "delete", "/eventsub/subscriptions", 204, params={"id": broadcaster.identifier}
        )
        broadcaster.identifier = None
        db_session.delete(notification, broadcaster)
        db_session.commit()
        self._result = ("", 204)


class StreamOnlineCreate(TwitchSubscribeCreate):

    def __init__(self, request) -> None:
        super().__init__("stream.online")
        self._guild: int = request.form.get("guild")
        self._channel: int = request.form.get("channel")
        self._login: str = request.form.get("broadcaster")
        self._message: str = request.form.get("message")
        self._creator_id: Optional[int] = session.user.id
        self._broadcaster: Optional[Broadcaster] = None

    def execute(self):
        self._get_broadcaster()
        self._condition = {"broadcaster_user_id": str(self._broadcaster.id)}
        super().execute()
        self._save_notification()

    def _get_broadcaster(self):
        self._broadcaster = db_session.query(Broadcaster).filter_by(login=self._login.lower()).first()

    def _save_notification(self) -> None:
        notification_id = self._response.get("data", [{}])[0].get("id")
        notification = Notification(
            identifier=notification_id,
            platform="twitch",
            guild_id=self._guild,
            channel_id=self._channel,
            broadcaster_id=self._broadcaster.id,
            body=self._message,
            creator_id=self._creator_id
        )
        db_session.add(notification)
        db_session.commit()


class StreamOnlineDelete(TwitchSubscribeDelete):
    pass


class UserUpdateCreate(TwitchSubscribeCreate):

    def __init__(self, request):
        super().__init__("user.update")
        self._login = request.form.get("broadcaster")
        self._broadcaster: Optional[Broadcaster] = None

    def execute(self):
        self._get_broadcaster()
        if not self._broadcaster.identifier:
            self._condition = {"user_id": str(self._broadcaster.id)}
            super().execute()
            self._set_identifier()

    def _get_broadcaster(self) -> None:
        broadcaster = db_session.query(Broadcaster).filter_by(login=self._login.lower()).first()
        if broadcaster:
            self._broadcaster = broadcaster
        else:
            self._request_broadcaster()
            self._save_broadcaster()

    def _request_broadcaster(self) -> None:
        data = {"login": self._login}
        response = twitch_api_request(
            "get", "/users/", params=data
        )
        broadcaster = response.get("data", [{}])[0]
        if not broadcaster:
            raise NotFound("Twitch user with such nickname not found")
        self._broadcaster = broadcaster

    def _save_broadcaster(self) -> None:
        broadcaster = Broadcaster(
            id=self._broadcaster.get("id"),
            login=self._broadcaster.get("login"),
            name=self._broadcaster.get("name")
        )
        db_session.add(broadcaster)
        db_session.commit()

    def _set_identifier(self):
        identifier = self._response.get("data", [{}])[0].get("id")
        self._broadcaster.identifier = identifier
        db_session.merge(self._broadcaster)
        db_session.commit()


class UserUpdateDelete(TwitchSubscribeDelete):
    pass
