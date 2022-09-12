from flask import session

from datetime import datetime
from sqlalchemy import and_

from front.base.utils import send_socket_message

from models import session as db_session
from models import UserSession


def user_middleware():
    if token := session.get("token"):
        user_session = db_session.query(UserSession).filter(and_(
            UserSession.access_token == token,
            UserSession.expires_in > datetime.now()
        )).first()
        if user_session and user_session.user:
            session.user = user_session.user
        else:
            session.pop("token")


def bot_middleware():
    if not session.get("bot"):
        bot_info = send_socket_message("bot_info")
        session["bot"] = bot_info
