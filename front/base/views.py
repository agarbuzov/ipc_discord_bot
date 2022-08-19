import settings

from datetime import datetime
from datetime import timedelta

from flask import redirect
from flask import session
from flask import url_for
from flask import request
from flask import Response
from flask import render_template
from flask.views import MethodView

from front.base.utils import send_socket_message
from front.base.utils import discord_api_request
from front.base.decorators import token_required

from models import User
from models import UserSession
from models import session as db_session


class Index(MethodView):

    @staticmethod
    @token_required
    def get():
        return render_template("index.html")


class Login(MethodView):

    @staticmethod
    def get():
        if session.get("token"):
            return redirect(url_for("index"))
        client_id = settings.DISCORD_CLIENT_ID
        return render_template("login.html", client_id=client_id)


class Auth(MethodView):

    def __init__(self):
        self.code = request.args.get("code")
        self.auth_data = self.get_auth_data()
        self.user_data = self.get_user_data()

    def get(self):
        user = User(**self.user_data)
        user_session = UserSession(**self.auth_data, user=user)
        db_session.merge(user_session, user)
        db_session.commit()
        session["token"] = self.auth_data.get("access_token")
        session["token_type"] = self.auth_data.get("token_type")
        return redirect(url_for("index"))

    def get_auth_data(self) -> dict:
        path = "/oauth2/token"
        data = {
            "code": self.code,
            "client_id": settings.DISCORD_CLIENT_ID,
            "client_secret": settings.DISCORD_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": url_for("auth", _external=True)
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = discord_api_request("post", path, data=data, headers=headers)
        data["expires_in"] = datetime.now() + timedelta(seconds=data.get("expires_in"))
        return data

    def get_user_data(self) -> dict:
        path = "/v10/users/@me"
        headers = {"Authorization": f"{self.auth_data.get('token_type')} {self.auth_data.get('access_token')}"}
        data = discord_api_request("get", path, headers=headers)
        return data


class Logout(MethodView):

    @staticmethod
    def post():
        session.pop("token")
        return redirect(url_for("login"))


class Profile(MethodView):

    @staticmethod
    @token_required
    def get():
        pass
