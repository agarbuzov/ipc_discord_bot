from fastapi import status

from fastapi.exceptions import HTTPException


class Forbidden(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN,
                         detail="You are not allowed to enter here")


class WebsocketUnavailable(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                         detail="Websocket is unavailable")
