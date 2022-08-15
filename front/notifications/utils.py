import settings
import requests

from datetime import datetime
from datetime import timedelta

from flask import current_app as app

from werkzeug.exceptions import BadRequest


def twitch_api_request(method, path, status_code=200, **kwargs) -> dict:
    url = "https://api.twitch.tv/helix"+path
    headers = {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": "Bearer t5rf3fk0r7do0lelpy0o275en66q98"
    }
    response = requests.request(method, url, headers=headers, **kwargs)
    data = response.json()
    if response.status_code != status_code:
        error = data.get("message")
        raise BadRequest(error)
    return data


def get_twitch_token():
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=data)
    auth_data = response.json()
    twitch_token = f"{auth_data.get('token_type').capitalize()} {auth_data.get('access_token')}"
    twitch_token_expires = datetime.now() + timedelta(seconds=auth_data.get("expires_in"))
    app.twitch_token = twitch_token
    app.twitch_token_expires = twitch_token_expires
