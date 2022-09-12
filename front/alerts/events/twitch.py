from typing import Optional

from flask import session

from sqlalchemy.orm.query import Query

from models import session as db_session
from models import Alert
from models import Broadcaster

from front.base.utils import twitch_api_request
from front.base.utils import send_socket_message
from front.base.events.twitch import TwitchEvent
from front.base.events.twitch import TwitchSubscriptionDelete
from front.base.events.twitch import TwitchSubscriptionCreate

from werkzeug.exceptions import NotFound


class StreamOnline(TwitchEvent):

    def __init__(self, request) -> None:
        super().__init__(request)

    def _handle_notification(self) -> None:
        broadcaster_id = self._request.json.get("event", {}).get("broadcaster_user_id")
        subscription_id = self._request.json.get("subscription", {}).get("id")
        if db_session.query(Alert).filter_by(identifier=subscription_id).first():
            send_socket_message("send_alert", {"broadcaster_id": broadcaster_id})
        self._result = ("", 204)

    def _handle_revocation(self) -> None:
        identifier = self._request.json.get("subscription", {}).get("id")
        alerts = db_session.query(Alert).filter_by(identifier=identifier)
        broadcaster = alerts.first().broadcaster
        twitch_api_request("delete", "/eventsub/subscriptions", 204, params={"id": broadcaster.identifier})
        broadcaster.identifier = None
        db_session.add(broadcaster)
        db_session.delete(alerts.all())
        db_session.commit()
        self._result = ("", 204)


class StreamOnlineCreate(TwitchSubscriptionCreate):

    def __init__(self, request) -> None:
        super().__init__("stream.online")
        self._guild: int = request.form.get("guild")
        self._channel: int = request.form.get("channel")
        self._login: str = request.form.get("broadcaster")
        self._message: str = request.form.get("message")
        self._creator_id: Optional[int] = session.user.id
        self._broadcaster: Optional[Broadcaster] = None
        self._subscription: Optional[Alert] = None

    def execute(self):
        self._get_broadcaster()
        self._get_subscriptions()
        if not self._subscription:
            self._condition = {"broadcaster_user_id": str(self._broadcaster.id)}
            super().execute()
        self._save_subscription()

    def _get_subscriptions(self):
        self._subscription = db_session.query(Alert).filter_by(broadcaster=self._broadcaster).first()

    def _get_broadcaster(self):
        self._broadcaster = db_session.query(Broadcaster).filter_by(login=self._login.lower()).first()

    def _save_subscription(self) -> None:
        if not self._subscription:
            subscription_id = self._response.get("data", [{}])[0].get("id")
        else:
            subscription_id = self._subscription.identifier
        alert = Alert(
            identifier=subscription_id,
            platform="twitch",
            guild_id=self._guild,
            channel_id=self._channel,
            broadcaster_id=self._broadcaster.id,
            body=self._message,
            creator_id=self._creator_id
        )
        db_session.add(alert)
        db_session.commit()


class StreamOnlineDelete(TwitchSubscriptionDelete):

    def __init__(self, request) -> None:
        super().__init__(request.form.get("id"))
        self._subscriptions: Optional[Query] = None
        self._subscription: Optional[Alert] = None

    def execute(self):
        self._get_subscriptions()
        if self._subscription and len(self._subscriptions.all()) == 1:
            super().execute()
        self._delete_record()

    def _get_subscriptions(self):
        self._subscriptions = db_session.query(Alert).filter_by(identifier=self._event_id)
        self._subscription = self._subscriptions.filter_by(creator_id=session.user.id).first()

    def _delete_record(self):
        db_session.delete(self._subscription)
        db_session.commit()


class UserUpdateCreate(TwitchSubscriptionCreate):

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
        response = twitch_api_request("get", "/users/", params=data)
        broadcaster = response.get("data", [{}])[0]

        if not broadcaster:
            raise NotFound("Twitch user with such nickname not found")

        self._broadcaster = Broadcaster(
            id=broadcaster.get("id"),
            login=broadcaster.get("login"),
            name=broadcaster.get("name")
        )

    def _save_broadcaster(self) -> None:
        db_session.add(self._broadcaster)
        db_session.commit()

    def _set_identifier(self):
        identifier = self._response.get("data", [{}])[0].get("id")
        self._broadcaster.identifier = identifier
        db_session.merge(self._broadcaster)
        db_session.commit()


class UserUpdateDelete(TwitchSubscriptionDelete):
    pass
