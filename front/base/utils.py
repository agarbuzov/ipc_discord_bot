import json
import requests
import settings

from flask import current_app as app

from contextlib import closing
from datetime import datetime
from datetime import timedelta
from websocket import create_connection

from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import ServiceUnavailable


def discord_api_request(method, path, **kwargs) -> dict:
    url = "https://discord.com/api"+path
    response = requests.request(method, url, **kwargs)
    data = response.json()
    if response.status_code != 200:
        error = data.get("error_description")
        raise BadRequest(error)
    return data


def send_socket_message(event, data=None) -> dict:
    try:
        with closing(create_connection("ws://localhost:5005")) as ws:
            ws.send(json.dumps({"event": event, "data": data}))
            response = json.loads(ws.recv())
    except ConnectionRefusedError:
        raise ServiceUnavailable
    return response


def twitch_api_request(method, path, status_code=200, **kwargs) -> dict:
    if not app.twitch_token or datetime.now() >= app.twitch_token_expires:
        get_twitch_token()
    url = "https://api.twitch.tv/helix"+path
    headers = {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": app.twitch_token
    }
    response = requests.request(method, url, headers=headers, **kwargs)
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        data = response.json()
    else:
        data = None
    if response.status_code != status_code:
        error = data.get("message")
        raise BadRequest(f"Twitch request error: {error}")
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
