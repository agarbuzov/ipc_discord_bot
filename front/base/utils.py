import json
import requests
import settings

from models import Token

from contextlib import closing
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
    token = Token.get_twitch()
    url = "https://api.twitch.tv/helix"+path
    headers = {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": f"{token.token_type} {token.token}"
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
