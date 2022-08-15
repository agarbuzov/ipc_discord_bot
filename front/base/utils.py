import json
import requests

from contextlib import closing

from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import ServiceUnavailable

from websocket import create_connection


def discord_api_request(method, path, **kwargs) -> dict:
    url = "https://discord.com/api"+path
    response = requests.request(method, url, **kwargs)
    data = response.json()
    if response.status_code != 200:
        error = data.get("error_description")
        raise BadRequest(error)
    return data


def send_sock_msg(event, data=None) -> dict:
    try:
        with closing(create_connection("ws://localhost:5005")) as ws:
            ws.send(json.dumps({"event": event, "data": data}))
            response = json.loads(ws.recv())
    except ConnectionRefusedError:
        raise ServiceUnavailable
    return response
